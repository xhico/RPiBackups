# -*- coding: utf-8 -*-
# !/usr/bin/python3

import json
import os
import shutil
import socket
import traceback
import logging
from Misc import get911, sendEmail


def main():
    # Get the hostname of the current device
    hostname = str(socket.gethostname()).upper()
    logger.info("hostname: " + hostname)

    # Restore
    bak_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bak")
    for root, dirs, files in os.walk(bak_folder):
        for file in files:
            source_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(source_file_path, bak_folder)
            if relative_path.startswith(hostname):
                relative_path = relative_path.replace(hostname + "_", "").replace("_SLASH_", "/").replace(".bak", "")
                logger.info(relative_path)
                shutil.copy(source_file_path, relative_path)

    return


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
