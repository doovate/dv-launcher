from dv_launcher.data.constants import Constants
from dv_launcher.services.docker.compose import run_command_in_service, run_command_in_running_service
from dv_launcher.services.logging.custom_logger import CustomLogger

logger = CustomLogger()


def update_admin_user(constants: Constants) -> None:
    """
    Updates the admin user password and username in the odoo database
    Args:
        constants: Configuration constants
    Returns: None
    """
    logger.print_status("Updating admin user password and username")

    if not all([constants.INITIAL_DB_USER_PASS, constants.INITIAL_DB_USER, ]):
        logger.print_warning("No admin user credentials provided, skipping admin user update")
        return
    command = f"""psql -U odoo -d {constants.INITIAL_DB_NAME} -c "UPDATE res_users SET login='{constants.INITIAL_DB_USER}', password='{constants.INITIAL_DB_USER_PASS}' WHERE id=2;" """

    try:
        run_command_in_running_service(constants, f"{constants.COMPOSE_PROJECT_NAME}_db", command)
    except Exception as e:
        logger.print_error(f"Error updating admin user: {str(e)}, skipping admin user update")
        return

    logger.print_success("Admin user updated successfully")


def create_database(constants: Constants) -> None:
    """
    Creates the initial odoo database
    Args:
        constants: Configuration constants
    """
    logger.print_status("Creating database")

    # Validate that we have the necessary credentials
    if not all([
        constants.INITIAL_DB_NAME,
        constants.INITIAL_DB_MASTER_PASS,
        constants.INITIAL_DB_USER_PASS
    ]):
        logger.print_warning("No database credentials provided, skipping database creation")
        return

    command = f"odoo -d {constants.INITIAL_DB_NAME} --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo --init=base --stop-after-init --without-demo=all"

    try:
        run_command_in_service(constants, "odoo", command)
    except Exception as e:
        logger.print_error(f"Error creating database: {e}, skipping database creation")

    logger.print_success(f"Database {constants.INITIAL_DB_NAME} created successfully")
    update_admin_user(constants)
