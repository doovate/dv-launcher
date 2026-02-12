import time

import requests

from dv_launcher.data.constants import Constants
from dv_launcher.services.logging.custom_logger import CustomLogger

logger = CustomLogger()


async def check_service_health(constants: Constants) -> None:
    max_attempts = 20
    attempt = 1
    wait_time = 0.25

    url = f"http://localhost:{constants.ODOO_EXPOSED_PORT}/web/health"

    logger.print_status(f"Checking odoo state on: {url} for {wait_time * max_attempts} seconds")

    while attempt <= max_attempts:
        try:
            response = requests.get(url, allow_redirects=False)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "pass":
                    logger.print_success(f"Odoo is working properly on: http://localhost:{constants.ODOO_EXPOSED_PORT}")
                    return
        except requests.RequestException:
            pass

        time.sleep(wait_time)
        attempt += 1

    logger.print_error("Check service logs")
    logger.print_error(f"Service not available on {url} after {max_attempts * wait_time} seconds")
