import subprocess
from typing import Optional

from dv_launcher.data.constants import Constants
from dv_launcher.services.logging.custom_logger import CustomLogger

logger = CustomLogger()


def stop_containers(constants: Constants) -> None:
    """
    Stops all running containers of this deployment
    """
    logger.print_header("STOPPING RUNNING CONTAINERS")

    try:
        logger.print_status("Stopping running containers")
        subprocess.run(
            "docker compose down",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            cwd=constants.BASE_DIR
        )

        logger.print_success("Running containers were successfully stopped")
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error stopping running containers: {str(e)}")
        logger.print_critical(f"Aborting deployment: {e.stderr}")
        exit(1)


def build_images(constants: Constants) -> None:
    """
    Builds docker images from docker-compose file
    """
    logger.print_header("APPLYING CONFIGURATION CHANGES")
    try:
        logger.print_status("Building container images")
        subprocess.run(
            "docker compose build",
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=constants.BASE_DIR
        )
        logger.print_success("Container images were successfully built")
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error building docker images: {str(e)} \n {e.stderr} \n {e.stdout}")
        exit(1)


def start_containers(constants: Constants, services: Optional[list[str]] = None) -> None:
    """
    Starts docker containers. If services are specified, only those will be started.

    Args:
        constants: Configuration constants
        services: List of service names to start (e.g., ['db', 'odoo']). If None, all services start.
    """
    try:
        logger.print_status("Spinning up containers")

        services_str = ' '.join(services) if services else ''
        cmd = f"docker compose up -d {services_str}".strip()

        subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=constants.BASE_DIR
        )
        logger.print_success("Containers were successfully started")
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error launching containers: {str(e)}")
        logger.print_critical(f"Aborting deployment: {e.stderr}")
        show_logs_on_error(constants)
        exit(1)


def run_command_in_service(constants: Constants, service: str, command: str) -> None:
    """
    Runs a command inside a specific service container

    Args:
        constants: Configuration constants
        service: Service name (e.g., 'odoo', 'db')
        command: Command to execute inside the container
    """
    try:
        cmd = f"docker compose run --rm {service} {command}"
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=constants.BASE_DIR
        )
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error running command in {service}: {str(e)}")
        logger.print_critical(f"{e.stderr}")
        show_logs_on_error(constants)
        raise


def run_command_in_running_service(constants: Constants, service: str, command: str) -> None:
    """
    Runs a command inside a specific running service container

    Args:
        constants: Configuration constants
        service: Service name (e.g., 'odoo', 'db')
        command: Command to execute inside the container
    """
    try:
        cmd = f"docker exec {service} {command}"
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=constants.BASE_DIR
        )
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error running command in running service {service}: {str(e)}")
        logger.print_critical(f"{e.stderr}")
        show_logs_on_error(constants)
        raise



def show_logs_on_error(constants: Constants) -> None:
    """
    Shows the last 30 lines of docker compose logs when an error occurs
    """
    logger.print_header("FAILURE LOGS")

    logger.print_status("Displaying Docker container logs:")
    try:
        cmd = "docker compose logs --tail=30"
        output = subprocess.check_output(cmd, shell=True, cwd=constants.BASE_DIR).decode()
        logger.print_warning(output)
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error getting Docker logs: {str(e)}")
