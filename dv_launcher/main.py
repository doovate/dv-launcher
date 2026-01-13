import typer

from dv_launcher.cli import config, db, deploy, init
from dv_launcher.cli.version import version

app = typer.Typer(
    add_completion=True,
    help="Odoo Deploy command line tool"
)

# Add all command groups
app.add_typer(config.app, name="config")
app.add_typer(db.app, name="db")

# Add direct commands
app.command(name="init")(init.init)
app.command(name="version")(version)

# Register the main deploy command as the default callback
app.callback(invoke_without_command=True)(deploy.main)


def main():
    """Main entry point for the CLI"""
    app()


if __name__ == "__main__":
    main()
