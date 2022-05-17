import os
import subprocess

import click
from github import Github


@click.command()
@click.option('--tag', prompt='notebook tag',
              help='The pangeo notebook tag to pull.')
@click.option('--feedstock-spec', prompt='feedstock spec')
@click.option('--recipe-path', prompt='recipe module path')
@click.option('--recipe-instance-name', prompt='recipe instance name')
def pull_and_run(tag, feedstock_spec, recipe_path, recipe_instance_name):
    """Pull the specified pangeo-notebook tag."""

    def check_output(command):
        output = subprocess.check_output(command)
        click.echo(output)
        return output

    # Pull the image
    notebook_img = f"pangeo/pangeo-notebook:{tag}"
    check_output(f"docker pull {notebook_img}".split())

    # Start the sibling container https://stackoverflow.com/a/30209974
    container_id = check_output(f"docker run -d {notebook_img} tail -f /dev/null".split())
    # Question: how reliable is it that `click.echo` will terminate in "\\n"?
    container_id = container_id.decode(encoding="utf-8").replace("\\n", "")

    # Get the recipe module as plain text
    recipe_module = (
        Github().get_repo(feedstock_spec)
        .get_contents(recipe_path).decoded_content.decode()
    )

    # Execute all commands within the notebook environment
    cmd_base = f"docker exec {container_id} conda run -n notebook"
    
    # Install pangeo-forge-recipes
    # (This can be removed once pangeo-forge-recipes is in noteboook image)
    # https://github.com/pangeo-data/pangeo-docker-images/issues/326
    check_output(f"{cmd_base} mamba install pangeo-forge-recipes".split())

    # Run a command in the sibling container
    check_output(
        f"{cmd_base} python3 -c".split()
        # NOTE: This command could be replaced with something more useful, such as importing a
        # a recipe and printing a list of `dict_object` keys to stdout. Or registering a recipe
        # with Prefect using a provided script.
        + [recipe_module + f"print({recipe_instance_name})"]
    )

    # Stop the sibling container
    check_output(f"docker stop {container_id}".split())

if __name__ == '__main__':
    pull_and_run()
