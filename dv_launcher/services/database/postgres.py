import subprocess
from typing import Optional

from dv_launcher.data.constants import Constants
from dv_launcher.services.logging.custom_logger import CustomLogger

logger = CustomLogger()


def wait_for_ready(constants: Constants, max_retries: int = 10) -> bool:
    """
    Waits for PostgreSQL to be ready to accept connections

    Args:
        constants: Configuration constants
        max_retries: Maximum number of retries

    Returns:
        True if PostgreSQL is ready, False otherwise
    """
    for i in range(max_retries):
        try:
            cmd = f"docker exec {constants.COMPOSE_PROJECT_NAME}_db pg_isready -U odoo"
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=constants.BASE_DIR,
            )

            if "accepting connections" in result.stdout:
                logger.print_success("PostgreSQL is ready!")
                return True

        except subprocess.CalledProcessError:
            if i == max_retries - 1:
                logger.print_error("PostgreSQL failed to become ready")
                return False

    return False


def list_all_databases(constants: Constants, max_retries: int = 10) -> Optional[list[str]]:
    """
    Lists all databases in PostgreSQL

    Args:
        constants: Configuration constants
        max_retries: Maximum number of retries

    Returns:
        List of all database names, or None if failed
    """
    for i in range(max_retries):
        try:
            # Wait for PostgreSQL to be ready
            if not wait_for_ready(constants, max_retries=30):
                continue

            cmd = f"docker exec {constants.COMPOSE_PROJECT_NAME}_db psql -U odoo -l -A"
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=constants.BASE_DIR,
            )

            # Parse the output to extract database names
            lines = result.stdout.split('\n')
            databases = []

            for line in lines:
                if '|' in line:
                    db_name = line.split('|')[0].strip()
                    databases.append(db_name)

            return databases

        except subprocess.CalledProcessError as e:
            if i >= max_retries - 1:
                logger.print_warning(
                    f"Failed getting databases names on try {i + 1}: \n{str(e)} \n{e.stderr} \n{e.stdout}")

    return None


def get_user_databases(constants: Constants) -> Optional[list[str]]:
    """
    Gets only user-created databases (filters out system databases)

    Args:
        constants: Configuration constants

    Returns:
        List of user database names, or None if failed
    """
    all_databases = list_all_databases(constants)

    if all_databases is None:
        return None

    # System databases to exclude
    system_dbs = {'template_postgis', 'postgres', 'template0', 'template1', 'Name'}

    # Filter out system databases and entries with '='
    user_databases = [
        db for db in all_databases
        if db not in system_dbs and '=' not in db and db.strip()
    ]

    return user_databases
