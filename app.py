import click
import subprocess

@click.command()
@click.option('--tag', prompt='notebook tag',
              help='The pangeo notebook tag to pull.')
def pull_img(tag):
    """Pull the specified pangeo-notebook tag."""

    def check_output(command):
        output = subprocess.check_output(command)
        click.echo(output)

    img = f"pangeo/pangeo-notebook:{tag}"
    click.echo(f"Pulling '{img}'!")
    check_output(["docker", "pull", img])
    


if __name__ == '__main__':
    pull_img()
