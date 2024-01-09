# -*- coding: utf-8 -*-
# !/usr/bin/python3

import json
import os
import shutil
import socket
import traceback
import logging
import paramiko
from Misc import get911, sendEmail


def setSSHConnection(copyDevice):
    """
    Establish an SSH connection and return an SFTP object.

    Args:
        copyDevice (str): The name of the device for which an SSH connection is required.

    Returns:
        paramiko.SFTP: An SFTP object for file transfer over SSH.
    """
    sftp, max_retries = None, 3
    for _ in range(max_retries):
        try:
            # Get SSH_CONFIG from configuration
            logger.info("Try to connect to " + copyDevice)
            SSH_CONFIG = config[copyDevice]["SSH_CONFIG"]

            # Get SSH configuration parameters from a function named get911
            SSH_CONFIG["IP"] = get911(copyDevice + "_SSH_CONFIG")["ip"]
            SSH_CONFIG["PORT"] = get911(copyDevice + "_SSH_CONFIG")["port"]
            SSH_CONFIG["USER"] = get911(copyDevice + "_SSH_CONFIG")["user"]
            SSH_CONFIG["PASSPHRASE"] = get911(copyDevice + "_SSH_CONFIG")["passphrase"]

            # Create an SSH client instance
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Load the private key with passphrase
            private_key = paramiko.RSAKey.from_private_key_file(SSH_CONFIG["PRIVATE_KEY"], password=SSH_CONFIG["PASSPHRASE"])

            # Establish an SSH connection
            ssh.connect(hostname=SSH_CONFIG["IP"], port=SSH_CONFIG["PORT"], username=SSH_CONFIG["USER"], pkey=private_key)

            # Open an SFTP session over the SSH connection
            sftp = ssh.open_sftp()
            if sftp is not None:
                break
        except Exception as ex:
            logger.error("Failed to connect to " + copyDevice)

    return sftp


def main():
    """
    Main function to copy and manage files to other devices over SSH.

    Returns:
        None
    """
    # Get the hostname of the current device
    hostname = str(socket.gethostname()).upper()
    logger.info("hostname: " + hostname)

    # Create the bak_folder if it doesn't exist
    bak_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bak")
    if not os.path.exists(bak_folder):
        os.makedirs(bak_folder)

    # Find other devices to copy to
    copyToDevices = [item for item in config.keys()]
    for copyDevice in copyToDevices:
        logger.info("copyDevice: " + copyDevice)
        sftp = None

        if hostname != copyDevice:
            # Set up an SSH connection to the target device with a retry mechanism
            sftp = setSSHConnection(copyDevice)

            # Send email if failed to connect
            if sftp is None:
                logger.info("Sending error email")
                sendEmail(os.path.basename(__file__), "Failed to connect to " + copyDevice)

        # Iterate over every file to copy
        LOCAL_PATHS = config[hostname]["LOCAL_PATHS"]
        for localPath in LOCAL_PATHS:
            logger.info("localPath: " + localPath)

            # Generate a backup file name based on timestamp, hostname, and localPath
            BAKFilename = hostname + "_" + localPath.replace("/", "_SLASH_") + ".bak"
            BAKFilePath = os.path.join(bak_folder, BAKFilename)

            # Copy/Send Files
            shutil.copyfile(localPath, BAKFilePath)
            if sftp is not None:
                sftp.put(localPath, BAKFilePath)

    return


if __name__ == '__main__':
    # Set Logging
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.abspath(__file__).replace(".py", ".log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
    logger = logging.getLogger()

    logger.info("----------------------------------------------------")

    # Load configuration from JSON file
    configFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(configFile) as inFile:
        config = json.load(inFile)

    try:
        main()
    except Exception as ex:
        logger.error(traceback.format_exc())
        sendEmail(os.path.basename(__file__), str(traceback.format_exc()))
    finally:
        logger.info("End")
