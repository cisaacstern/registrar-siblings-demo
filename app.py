import os

import click
import subprocess

@click.command()
@click.option('--tag', prompt='notebook tag',
              help='The pangeo notebook tag to pull.')
def pull_and_run(tag):
    """Pull the specified pangeo-notebook tag."""

    def check_output(command):
        output = subprocess.check_output(command)
        click.echo(output)

    recipe_handler_image = f"pangeo/pangeo-notebook:{tag}"
    click.echo(f"Pulling '{recipe_handler_image}'!")
    check_output(["docker", "pull", recipe_handler_image])
    
    check_output(
        [
            "docker",
            "run",
            "-it",
            "-v",
            "submodule:/home/jovyan/submodule",
            recipe_handler_image,
            "python3",
            "submodule/import_recipe.py",
        ]
    )

if __name__ == '__main__':
    pull_and_run()
