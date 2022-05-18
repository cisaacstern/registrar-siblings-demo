import subprocess

import click
from github import Github

SCRIPT_REPO = "cisaacstern/recipe-handler-demo"
ACTIONS = {
    "repr": "scripts/print_recipe_repr.py"
}


def check_output(command):
    output = subprocess.check_output(command)
    click.echo(output)
    return output


@click.command()
@click.option(
    '--tag',
    prompt='notebook tag',
    default='latest',
)
@click.option(
    '--feedstock-spec',
    prompt='feedstock spec',
    default="pangeo-forge/noaa-coastwatch-geopolar-sst-feedstock",
)
@click.option(
    '--recipe-path',
    prompt='recipe module path',
    default="feedstock/recipe.py",
)
@click.option(
    '--recipe-instance-name',
    prompt='recipe instance name',
    default="recipe",
)
@click.option('--action', prompt='action')
def pull_and_run(tag, feedstock_spec, recipe_path, recipe_instance_name, action):
    """Pull the specified pangeo-notebook tag."""

    g = Github()

    # Pull the image
    notebook_img = f"pangeo/pangeo-notebook:{tag}"
    check_output(f"docker pull {notebook_img}".split())

    # Start the sibling container https://stackoverflow.com/a/30209974
    container_id = check_output(f"docker run -d {notebook_img} tail -f /dev/null".split())

    # Question: how reliable is it that `subprocess.check_output` will terminate in "\\n"?
    container_id = container_id.decode(encoding="utf-8").replace("\\n", "")

    # Execute all commands within the notebook environment
    cmd_base = f"docker exec {container_id} conda run -n notebook".split()

    # Get the recipe module as plain text and cache it
    recipe_module = g.get_repo(feedstock_spec).get_contents(recipe_path).decoded_content.decode()

    adaptor = f"\nrecipe_instance = {recipe_instance_name}\n"

    coda = (
        g.get_repo(SCRIPT_REPO).get_contents(ACTIONS[action], ref=tag).decoded_content.decode()
    )

    # Run a script in the sibling container, with the cached recipe as input
    check_output(cmd_base + ["python3", "-c", f"{recipe_module + adaptor + coda}"])

    # Stop the sibling container
    check_output(f"docker stop {container_id}".split())

if __name__ == '__main__':
    pull_and_run()
