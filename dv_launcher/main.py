import typer

from dv_launcher.cli import config, db, deploy, init
from dv_launcher.cli.version import version
from dv_launcher.services.logging.custom_logger import CustomLogger, CustomLogFormatter

logger = CustomLogger()

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
@app.callback(invoke_without_command=True)
def main(
        ctx: typer.Context,
        color: bool = typer.Option(
            True,
            "--color/--no-color",
            help="Enable colored output",
            is_eager=True,
            # expose_value=False
        ),
):
    logger.configure(colored_output=color)

    ctx.ensure_object(dict)
    ctx.obj["color"] = color
    ctx.obj["logger"] = logger
    deploy.main(ctx)

    # if ctx.invoked_subcommand is None:
    #     deploy.main(ctx)


# def main():
#     """Main entry point for the CLI"""
    # app()


if __name__ == "__main__":
    # main()
    app()