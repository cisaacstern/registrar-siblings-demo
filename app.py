import click
import docker
from docker.models.containers import Container
from github import Github

SCRIPT_REPO = "cisaacstern/recipe-handler-demo"
ACTIONS = {
    "repr": "scripts/print_recipe_repr.py"
}


def echo_output(container: Container, command: list) -> None:
    output = container.exec_run(command).output
    click.echo(output.decode(encoding="utf-8"))


def bytestring_to_file(fname: str, bytestring: bytes) -> list:
    return [
        "python3",
        "-c",
        f"with open('{fname}', mode='wb') as f: f.write({bytestring})",
    ]


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
    d = docker.from_env()

    # Start the sibling container https://stackoverflow.com/a/30209974
    recipe_handler = d.containers.run(
        f"pangeo/pangeo-notebook:{tag}", "tail -f /dev/null", detach=True, auto_remove=True,
    )

    # Get the recipe module and script as plain text
    recipe_module_bytes = g.get_repo(feedstock_spec).get_contents(recipe_path).decoded_content
    script_bytes = (
        g.get_repo(SCRIPT_REPO).get_contents(ACTIONS[action], ref=tag).decoded_content
    )

    # Cache recipe + script into a subdirectory in the sibling container
    recipe_handler.exec_run(["bash", "-c", "mkdir pangeo-forge"])
    recipe_handler.exec_run(bytestring_to_file("pangeo-forge/recipe.py", recipe_module_bytes))
    recipe_handler.exec_run(bytestring_to_file("pangeo-forge/script.py", script_bytes))

    # echo_output(recipe_handler, ["ls", "-la"])
    # echo_output(recipe_handler, ["cat", "pangeo-forge/recipe.py"])
    # echo_output(recipe_handler, ["cat", "pangeo-forge/script.py"])

    # Call the script on the recipe (inside the sibling container's notebook environment)
    # TODO: If `recipe_object_name`` contains `:`, it's a dict-object, and parsed differently
    echo_output(
        recipe_handler,
        f"conda run -n notebook python3 pangeo-forge/script.py {recipe_object_name}".split(),
    )

    # Stop the sibling container
    recipe_handler.stop()

if __name__ == '__main__':
    pull_and_run()
