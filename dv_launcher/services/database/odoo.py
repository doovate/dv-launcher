from playwright.async_api import async_playwright
import httpx

from dv_launcher.data.constants import Constants
from dv_launcher.services.logging.custom_logger import CustomLogger

logger = CustomLogger()


async def update_admin_user(constants: Constants, port: str) -> None:
    """
    Updates the admin user login name using Odoo's JSON-RPC API
    Args:
        constants: Configuration constants
        port: Port where Odoo is running
    """
    logger.print_status(f"Updating admin user login to '{constants.INITIAL_DB_USER}'")

    url = f"http://localhost:{port}/jsonrpc"

    # First, authenticate to get the user ID
    auth_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "common",
            "method": "authenticate",
            "args": [
                constants.INITIAL_DB_NAME,
                "admin",
                constants.INITIAL_DB_USER_PASS,
                {}
            ]
        },
        "id": 1
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Authenticate
            auth_response = await client.post(
                url,
                json=auth_payload,
                headers={"Content-Type": "application/json"}
            )

            if auth_response.status_code != 200:
                logger.print_error(f"Failed to authenticate: HTTP {auth_response.status_code}")
                return

            auth_result = auth_response.json()
            if "error" in auth_result:
                logger.print_error(f"Authentication error: {auth_result['error']}")
                return

            uid = auth_result.get("result")
            if not uid:
                logger.print_error("Failed to get user ID")
                return

            # Update the user's login and name
            update_payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute",
                    "args": [
                        constants.INITIAL_DB_NAME,
                        uid,
                        constants.INITIAL_DB_USER_PASS,
                        "res.users",
                        "write",
                        [uid],
                        {
                            "login": constants.INITIAL_DB_USER,
                            "name": constants.INITIAL_DB_USER
                        }
                    ]
                },
                "id": 2
            }

            update_response = await client.post(
                url,
                json=update_payload,
                headers={"Content-Type": "application/json"}
            )

            if update_response.status_code == 200:
                update_result = update_response.json()
                if "error" in update_result:
                    logger.print_error(f"Failed to update user: {update_result['error']}")
                else:
                    logger.print_success(f"Admin user updated to '{constants.INITIAL_DB_USER}'")
            else:
                logger.print_error(f"Failed to update user: HTTP {update_response.status_code}")

    except Exception as e:
        logger.print_error(f"Error updating admin user: {e}")


async def create_database(constants: Constants, port: str = None) -> None:
    """
    Creates an Odoo database using Playwright to automate the web interface

    Args:
        constants: Configuration constants
        port: Port where Odoo is running (defaults to ODOO_EXPOSED_PORT from constants)
    """
    if port is None:
        port = constants.ODOO_EXPOSED_PORT

    logger.print_status("Creating database")

    for i in range(2):
        try:
            if constants.INITIAL_DB_NAME is not None and constants.INITIAL_DB_MASTER_PASS is not None and constants.INITIAL_DB_USER is not None and constants.INITIAL_DB_USER_PASS is not None:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(f"http://localhost:{port}/web/database/manager")
                    await page.fill("input[name=\"master_pwd\"]", constants.INITIAL_DB_MASTER_PASS)
                    await page.fill("input[name=\"name\"]", constants.INITIAL_DB_NAME)
                    await page.fill("input[name=\"login\"]", constants.INITIAL_DB_USER)
                    await page.fill("input[name=\"password\"]", constants.INITIAL_DB_USER_PASS)
                    await page.select_option('#lang', 'es_ES')
                    await page.select_option('#country', 'es')
                    await page.click("text=Create database")

                logger.print_success("Database created successfully")
                return
            else:
                logger.print_warning("No database credentials provided, skipping database creation")
                return
        except Exception as e:
            logger.print_error(f"Failed to create database: {e}")
            raise
