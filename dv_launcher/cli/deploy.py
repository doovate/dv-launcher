import asyncio
import os
import time

import typer

from dv_launcher.cli import config, db, version
from dv_launcher.cli.config import scaffold
from dv_launcher.data.constants import get_constants
from dv_launcher.services.logging.custom_logger import CustomLogger
from dv_launcher.services.orchestration import deployment

app = typer.Typer(
    add_completion=True,
    help="Odoo Deploy command line tool"
)

cwd = os.getcwd()
logger = CustomLogger()


async def async_main():
    """Main deployment function"""
    constants = get_constants(cwd)
    start_time = time.time()

    # Make sure the necessary directories and files exist
    scaffold()

    # Execute full deployment
    await deployment.deploy_full_stack(constants)

    end_time = time.time() - start_time
    logger.print_success(f"Total time: {end_time:.2f} seconds")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Launch and configure Odoo and PostgreSQL containers"""
    if not ctx.invoked_subcommand:
        asyncio.run(async_main())


# Add subcommands
app.add_typer(config.app, name="config")
app.add_typer(db.app, name="db")
app.add_typer(version.app, name="version")


def deploy():
    """Entry point for the CLI"""
    app()


if __name__ == "__main__":
    deploy()
