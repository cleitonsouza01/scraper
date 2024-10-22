import os
import sys

from loguru import logger


# Fetch log settings from environment variables
log_level = "INFO"
log_file_path = "backend.log"
log_rotation = "10 MB"
log_retention = "28 days"
log_compression = "zip"

default_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {message}"

# Configure Loguru
logger.remove()  # Remove the default logger configuration
logger.add(
    log_file_path,
    format=default_format,
    level=log_level,
    rotation=log_rotation,
    retention=log_retention,
    compression=log_compression
)

# Optional: Log to the console as well (with a different format if needed)
logger.add(
    sys.stdout,
    format=default_format,
    level=log_level
)
