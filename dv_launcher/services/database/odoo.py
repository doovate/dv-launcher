from playwright.async_api import async_playwright

from dv_launcher.data.constants import Constants
from dv_launcher.services.logging.custom_logger import CustomLogger

logger = CustomLogger()


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
