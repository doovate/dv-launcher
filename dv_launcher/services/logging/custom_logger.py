import logging


class CustomLogFormatter(logging.Formatter):
    """Formatter that adds styling to logs """

    # Color definitions using ANSI escape sequences
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(self, colored_output: bool = True):
        super().__init__()

        self.FORMATS = {
            logging.DEBUG: f"{self.CYAN}%(message)s{self.RESET}",
            logging.INFO: f"{self.BLUE}[STATUS] %(message)s{self.RESET}",
            logging.WARNING: f"{self.YELLOW}[WARNING] %(message)s{self.RESET}",
            logging.ERROR: f"{self.RED}[ERROR] %(message)s{self.RESET}",
            logging.CRITICAL: f"{self.RED}[CRITICAL] %(message)s{self.RESET}",
            25: f"{self.GREEN}[SUCCESS] %(message)s{self.RESET}"
        } if colored_output else {
            logging.DEBUG: "%(message)s",
            logging.INFO: "[STATUS] %(message)s",
            logging.WARNING: "[WARNING] %(message)s",
            logging.ERROR: "[ERROR] %(message)s",
            logging.CRITICAL: "[CRITICAL] %(message)s",
            25: "[SUCCESS] %(message)s"
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CustomLogger(logging.Logger):
    """Logger that uses the custom formatter"""

    _instance = None

    def __new__(cls, name: str = "odoo_deploy"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, name: str = "odoo_deploy"):
        if self._initialized:
            return

        super().__init__(name)
        self.name = name

        # Add success level to logs
        logging.addLevelName(25, "SUCCESS")

        self.log_level = logging.DEBUG

        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False



        self._initialized = True

    def configure(self, colored_output: bool = True):
        # Console handler
        console_handler = logging.StreamHandler()
        custom_log_formater = CustomLogFormatter(colored_output= colored_output)
        console_handler.setFormatter(custom_log_formater)
        console_handler.setLevel(self.log_level)
        self.logger.addHandler(console_handler)

    def print_header(self, message):
        """Print header"""
        self.logger.debug("=" * 60)
        self.logger.debug(message)
        self.logger.debug("=" * 60)

    def print_status(self, message):
        """Print info messages"""
        self.logger.info(message)

    def print_error(self, message):
        """Print error messages"""
        self.logger.error(message)

    def print_warning(self, message):
        """Print warning messages."""
        self.logger.warning(message)

    def print_critical(self, message):
        """Print critical messages."""
        self.logger.critical(message)

    def print_success(self, message):
        """Print success messages."""
        self.logger.log(25, message)
