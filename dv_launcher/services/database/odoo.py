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
    Creates an Odoo database using the JSON-RPC API
    Args:
        constants: Configuration constants
        port: Port where Odoo is running (defaults to ODOO_EXPOSED_PORT from constants)
    """
    if port is None:
        port = constants.ODOO_EXPOSED_PORT

    logger.print_status("Creating database")

    # Validate that we have the necessary credentials
    if not all([
        constants.INITIAL_DB_NAME,
        constants.INITIAL_DB_MASTER_PASS,
        constants.INITIAL_DB_USER_PASS
    ]):
        logger.print_warning("No database credentials provided, skipping database creation")
        return

    url = f"http://localhost:{port}/jsonrpc"

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "db",
            "method": "create_database",
            "args": [
                constants.INITIAL_DB_MASTER_PASS,
                constants.INITIAL_DB_NAME,
                False,
                "es_ES",
                constants.INITIAL_DB_USER_PASS
            ]
        },
        "id": 1
    }

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()

                    # Verify that the request was successful
                    if "error" in result:
                        error_msg = result["error"].get("data", {}).get("message", str(result["error"]))
                        logger.print_error(f"Odoo API error: {error_msg}")
                        raise Exception(error_msg)

                    logger.print_success("Database created successfully")

                    # Update admin user login if INITIAL_DB_USER is provided and different from "admin"
                    if constants.INITIAL_DB_USER and constants.INITIAL_DB_USER != "admin":
                        await update_admin_user(constants, port)

                    return
                else:
                    logger.print_error(f"HTTP {response.status_code}: {response.text}")
                    raise Exception(f"Failed with status code {response.status_code}")

        except httpx.TimeoutException:
            logger.print_error(f"Timeout creating database (attempt {attempt + 1}/2)")
            if attempt == 1:
                raise
        except Exception as e:
            logger.print_error(f"Failed to create database (attempt {attempt + 1}/2): {e}")
            if attempt == 1:
                raise
