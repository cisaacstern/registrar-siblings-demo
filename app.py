import os
import subprocess

import click

@click.command()
@click.option('--tag', prompt='notebook tag',
              help='The pangeo notebook tag to pull.')
def pull_and_run(tag):
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
        + ["import pangeo_forge_recipes; print(f'{pangeo_forge_recipes.__version__}=')"]
    )

    # Stop the sibling container
    check_output(f"docker stop {container_id}".split())

if __name__ == '__main__':
    pull_and_run()
