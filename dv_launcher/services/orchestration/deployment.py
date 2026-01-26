import asyncio
import os

from dv_launcher.data.constants import Constants
from dv_launcher.services.database import odoo as odoo_db, postgres
from dv_launcher.services.database_creator import check_service_health
from dv_launcher.services.docker import compose
from dv_launcher.services.files.addons import list_addons_in_folder, list_to_install_addons
from dv_launcher.services.files.file_operations import copy_requirements, list_updated_addons, update_addons_cache
from dv_launcher.services.files.traefik import update_proxy_mode
from dv_launcher.services.logging.custom_logger import CustomLogger

logger = CustomLogger()


async def deploy_full_stack(constants: Constants) -> None:
    """
    Complete deployment process: stops old containers, builds, deploys services,
    handles module installation/updates, and verifies deployment

    Args:
        constants: Configuration constants
    """
    # Copy the requirements.txt file to the addons folder
    copy_requirements(
        base_dir=constants.BASE_DIR,
        requirements_file=os.path.join(constants.ODOO_ADDONS, 'requirements.txt'),
    )

    # Stop running containers
    compose.stop_containers(constants)

    # Update proxy mode
    update_proxy_mode(os.getcwd(), constants.DEPLOYMENT_TARGET)

    # Build docker images
    compose.build_images(constants)

    # Deploy based on module management settings
    if constants.AUTO_INSTALL_MODULES or constants.AUTO_UPDATE_MODULES:
        await _deploy_with_modules(constants)
    else:
        await _deploy_without_modules(constants)

    # Verify deployment
    await _verify_deployment(constants)


async def _deploy_with_modules(constants: Constants) -> None:
    """
    Deployment process with module installation and updates
    """
    logger.print_header("UPDATING DATABASES AND INSTALLING MODULES")

    # Start only database
    compose.start_containers(constants, services=["db"])

    # Get database list
    database_list = postgres.get_user_databases(constants)

    if not database_list:
        await _handle_no_databases(constants)
    else:
        await _handle_existing_databases(constants, database_list)


async def _handle_no_databases(constants: Constants) -> None:
    """
    Handles deployment when no databases exist
    """

    # Create the database if auto-create is enabled
    if constants.AUTO_CREATE_DATABASE:
        odoo_db.create_database(constants)

        # Get the new database and install modules
        database_list = postgres.get_user_databases(constants)
        addons_list = list_addons_in_folder(constants.ADDONS_FOLDER)

        # Install addons for the new database
        _install_and_update_addons(constants, database_list, addons_list)

    # Launch containers
    logger.print_header("DEPLOYING ENVIRONMENT")
    compose.start_containers(constants)


async def _handle_existing_databases(constants: Constants, database_list: list[str]) -> None:
    """
    Handles deployment when databases already exist
    """
    addons_list = list_addons_in_folder(constants.ADDONS_FOLDER)

    # Determine which modules to update
    update_addons_list = []
    update_addons_json = {}

    if constants.UPDATE_MODULE_LIST:
        update_addons_string = constants.UPDATE_MODULE_LIST
    else:
        update_addons_list, update_addons_json = list_updated_addons(
            constants.ADDONS_FOLDER,
            constants.CACHE_ADDONS_FILE
        )
        update_addons_string = ','.join(update_addons_list)

    # Install and update modules for each database
    _install_and_update_addons(constants, database_list, addons_list, update_addons_list, update_addons_string)

    # Launch containers
    logger.print_header("DEPLOYING ENVIRONMENT")
    compose.start_containers(constants)

    # Update cache
    update_addons_cache(update_addons_json, constants.CACHE_ADDONS_FILE)


async def _deploy_without_modules(constants: Constants) -> None:
    """
    Simple deployment without module management
    """
    logger.print_header("DEPLOYING ENVIRONMENT")
    compose.start_containers(constants)

    # Create the database if needed
    if constants.DEPLOYMENT_TARGET == 'dev' and constants.AUTO_CREATE_DATABASE:
        database_list = postgres.get_user_databases(constants)
        if not database_list:
            await odoo_db.create_database(constants)


def _install_and_update_addons(constants: Constants, database_list: list[str], addons_list: list[str],
                               update_addons_list: list[str] = None, update_addons_string: str = None
                               ) -> None:
    # Force update option
    force_update = '--dev=all' if constants.FORCE_UPDATE else ''

    # Install and update modules for each database
    try:
        for db in database_list:
            # Install new modules
            install_addons_string = list_to_install_addons(constants, addons_list, db)
            if constants.AUTO_INSTALL_MODULES and install_addons_string:
                logger.print_status(f"Installing modules on database {db}")
                cmd = f"odoo -d {db} -i {install_addons_string} --stop-after-init"
                compose.run_command_in_service(constants, "odoo", cmd)
                logger.print_success(f"Installing modules on database {db} completed")

            # Update existing modules
            if constants.AUTO_UPDATE_MODULES and update_addons_list and update_addons_string:
                logger.print_status(f"Updating modules on database {db}")
                cmd = f"odoo -d {db} -u {update_addons_string} {force_update} --stop-after-init"
                compose.run_command_in_service(constants, "odoo", cmd)
                logger.print_success(f"Updating modules on database {db} completed")
    except Exception as e:
        logger.print_error(f"Error installing/updating modules: {e}")
        logger.print_warning("Skipping module installation/updates.")


async def _verify_deployment(constants: Constants) -> None:
    """
    Verifies that the deployment is healthy
    """
    logger.print_header("Verifying Odoo state")

    if constants.DEPLOYMENT_TARGET == 'prod':
        await asyncio.gather(
            check_service_health(constants),
            check_service_health(constants, constants.DOMAIN)
        )
    else:
        await check_service_health(constants)


def deploy_database_only(constants: Constants) -> None:
    """
    Starts only the database service
    """
    logger.print_status("Launching database")
    compose.start_containers(constants, services=["db"])


def deploy_odoo_only(constants: Constants) -> None:
    """
    Starts only the Odoo service
    """
    logger.print_status("Launching Odoo")
    compose.start_containers(constants, services=["odoo"])
