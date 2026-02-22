import logging
from pathlib import Path

LOG_FILE = "logs/app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"


def setup_logging():
    """Configure root logging once."""
    
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if logging.getLogger().handlers:
        return  # Already configured

    formatter = logging.Formatter(LOG_FORMAT)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress noisy libraries
    library_blocklist = [
        "httpcore",
        "httpx",
        "openai",
        "matplotlib",
        "gremlinpython",
        "azure",
        "mcp"
    ]

    for module in library_blocklist:
        logging.getLogger(module).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> logging.Logger:
    """Get a configured logger."""
    setup_logging()
    return logging.getLogger(name)
