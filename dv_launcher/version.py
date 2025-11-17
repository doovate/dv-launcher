import asyncio
import subprocess

import typer

from importlib.metadata import PackageNotFoundError, version as get_version
from playwright.async_api import async_playwright

from dv_launcher.services.custom_logger import CustomLogger

app = typer.Typer()


@app.command()
def version():
    pkg_version = get_version("dv-launcher")
    print(pkg_version)

if __name__ == "__main__":
    app()
