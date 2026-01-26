import asyncio
import os

import typer

from dv_launcher.data.constants import get_constants
from dv_launcher.services.database import odoo as odoo_db
from dv_launcher.services.logging.custom_logger import CustomLogger

app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    help="Database operations"
)

cwd = os.getcwd()
logger = CustomLogger()


@app.command(help="Create Odoo database")
def create(port: str = "8069"):
    """Create a new Odoo database via web interface"""
    asyncio.run(_create_database(port))


async def _create_database(port: str) -> None:
    """Internal async function to create database"""
    constants = get_constants(cwd)
    await odoo_db.create_database(constants)


if __name__ == "__main__":
    app()
