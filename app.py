import subprocess

import click
from github import Github

SCRIPT_REPO = "cisaacstern/recipe-handler-demo"
ACTIONS = {
    "repr": "scripts/print_recipe_repr.py"
}


def check_output(command, shell=False):
    output = subprocess.check_output(command, shell=shell)
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
    '--recipe-object-name',
    prompt='recipe object name',
    default="recipe",
)
@click.option('--action', prompt='action')
def pull_and_run(tag, feedstock_spec, recipe_path, recipe_object_name, action):
    """Pull the specified pangeo-notebook tag."""

    g = Github()

    # Pull the image
    notebook_img = f"pangeo/pangeo-notebook:{tag}"
    check_output(f"docker pull {notebook_img}".split())

    # Start the sibling container https://stackoverflow.com/a/30209974
    container_id = check_output(f"docker run --rm -d {notebook_img} tail -f /dev/null".split())

    # Question: how reliable is it that `subprocess.check_output` will terminate in "\\n"?
    container_id = container_id.decode(encoding="utf-8").replace("\\n", "")
    cmd_base = f"docker exec {container_id}".split()

    # Get the recipe module as plain text and cache it
    recipe_module_bytes = g.get_repo(feedstock_spec).get_contents(recipe_path).decoded_content

    script_bytes = (
        g.get_repo(SCRIPT_REPO).get_contents(ACTIONS[action], ref=tag).decoded_content
    )

    # Run a script in the sibling container, with the cached recipe as input
    check_output(cmd_base + ["bash", "-c", "mkdir pangeo-forge"])

    def bytestring_to_file(fname: str, bytestring: bytes) -> list:
        return [
            "python3",
            "-c",
            f"with open('pangeo-forge/{fname}', mode='wb') as f: f.write({bytestring})",
        ]

    check_output(cmd_base + bytestring_to_file("recipe.py", recipe_module_bytes))
    check_output(cmd_base + bytestring_to_file("script.py", script_bytes))
    # check_output(cmd_base + ["ls", "-la"])
    # check_output(cmd_base + ["cat", "pangeo-forge/recipe.py"])
    # check_output(cmd_base + ["cat", "pangeo-forge/script.py"])
    # if recipe_object_name contains a `:`, it can be interpreted as a dict-object, and handled differently
    run = f"conda run -n notebook python3 pangeo-forge/script.py {recipe_object_name}".split()
    check_output(cmd_base + run)

    # Stop the sibling container
    check_output(f"docker stop {container_id}".split())

if __name__ == '__main__':
    pull_and_run()
