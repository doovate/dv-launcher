from importlib.metadata import version as get_version

import typer

app = typer.Typer()


@app.command()
def version():
    pkg_version = get_version("dv-launcher")
    print(pkg_version)


if __name__ == "__main__":
    app()
