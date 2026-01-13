import configparser
import os
import subprocess

import psutil
import typer

from dv_launcher.services.logging.custom_logger import CustomLogger

app = typer.Typer(
    add_completion=True,
    help="Initialize Odoo repository"
)

base_dir = os.getcwd()

logger = CustomLogger()


@app.command(help="Initialize Odoo repository")
def init() -> None:
    logger.print_status("Cloning Odoo repository")

    # Especificar la URL del repositorio y el directorio destino
    repo_url = "https://github.com/doovate/dv-odoo-docker.git"
    destination_dir = os.path.join(base_dir, "odoo-docker")

    try:
        # Clone repository
        subprocess.run(
            ["git", "clone", repo_url, destination_dir],
            check=True,
            capture_output=True,
            text=True
        )
        logger.print_success(f"Repository cloned successfully to {destination_dir}")
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error cloning repository: {e.stderr}")
        raise typer.Exit(code=1)
    except FileNotFoundError:
        logger.print_error("Git is not installed or not in PATH")
        raise typer.Exit(code=1)
