# -*- coding: utf-8 -*-
# !/usr/bin/python3

import os
import shutil
import socket
import traceback
import logging
from Misc import get911, sendEmail


def main():
    """
    Main function to restore files from the 'bak' folder based on the current device's hostname.

    This function retrieves the current device's hostname, locates backup files in the 'bak' folder
    that match the hostname, and restores them to their original locations.

    Note: The backup files in the 'bak' folder must follow a naming convention with the hostname
    as a prefix.

    Returns:
        None
    """
    # Get the hostname of the current device
    hostname = str(socket.gethostname()).upper()
    logger.info(f"Hostname: {hostname}")

    # Restore files
    bak_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bak")
    for root, dirs, files in os.walk(bak_folder):
        for file in files:
            source_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(source_file_path, bak_folder)

            # Check if the backup file matches the current hostname
            if relative_path.startswith(hostname):
                # Modify the relative path to obtain the original file path
                relative_path = relative_path.replace(f"{hostname}_", "")
                relative_path = relative_path.replace("_SLASH_", "/")
                relative_path = relative_path.replace(".bak", "")
                logger.info(f"Restoring: {relative_path}")

                # Copy the backup file to its original location
                shutil.copy(source_file_path, relative_path)


if __name__ == '__main__':
    # Set Logging
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.abspath(__file__).replace(".py", ".log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
    logger = logging.getLogger()

    logger.info("----------------------------------------------------")

    try:
        main()
    except Exception as ex:
        logger.error(traceback.format_exc())
        sendEmail(os.path.basename(__file__), str(traceback.format_exc()))
    finally:
        logger.info("End")
