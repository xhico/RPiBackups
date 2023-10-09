# -*- coding: utf-8 -*-
# !/usr/bin/python3

import datetime
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
    # Get SSH_CONFIG from configuration
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

    return sftp


def cleanup_old_files(copyDevice, bak_folder, localPath):
    """
    Clean up old files in a specified folder.

    Args:
        copyDevice (str): The name of the device.
        bak_folder (str): The folder path where backup files are located.
        localPath (str): The local path used as a filter for deleting files.

    Returns:
        None
    """
    # Remove the current date and time prefix from localPath
    localPath = localPath.replace(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_", "")

    # Get the current date and time
    today = datetime.datetime.now()

    # List to store old files
    oldFiles = []

    # Iterate through files in the backup folder
    for filename in os.listdir(bak_folder):
        file_path = os.path.join(bak_folder, filename)

        # Get the creation time of the file
        creation_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

        # Check if the file is older than the specified number of days and matches the localPath
        if (today - creation_time).days > config[copyDevice]["KEEP_DAYS"] and localPath in file_path:
            oldFiles.append(file_path)

    # Dictionary to store the last file per day
    last_files_per_day = {}

    # Sort the old files by file path
    for file_path in sorted(oldFiles):
        date = file_path.split("/")[-1].split("_")[0]

        # Check if the file is the latest for the given date
        if date not in last_files_per_day or file_path > last_files_per_day[date]:
            last_files_per_day[date] = file_path

    # Convert the dictionary values to a list of the last files per day
    last_files_per_day = [file for _, file in last_files_per_day.items()]

    # Identify files to delete
    files_to_delete = [file for file in oldFiles if file not in last_files_per_day]

    # Delete identified files
    for file in files_to_delete:
        os.remove(file)

    # Log the number of files deleted
    logger.info("Deleted " + str(len(files_to_delete)) + " files")

    return


def main():
    """
    Main function to copy and manage files to other devices over SSH.

    Returns:
        None
    """
    # Get the hostname of the current device
    hostname = str(socket.gethostname()).upper()
    logger.info("hostname: " + hostname)

    # Find other devices to copy to
    copyToDevices = [item for item in config.keys() if item != hostname]
    for copyDevice in copyToDevices:
        logger.info("copyDevice: " + copyDevice)

        # Set up an SSH connection to the target device
        sftp = setSSHConnection(copyDevice)

        # Create the bak_folder if it doesn't exist
        bak_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bak")
        if not os.path.exists(bak_folder):
            os.makedirs(bak_folder)

        # Iterate over every file to copy
        LOCAL_PATHS = config[hostname]["LOCAL_PATHS"]
        for localPath in LOCAL_PATHS:
            logger.info("localPath: " + localPath)

            # Generate a backup file name based on timestamp, hostname, and localPath
            BAKFilename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + hostname + "_" + localPath.replace("/", "_SLASH_") + ".bak"
            BAKFilePath = os.path.join(bak_folder, BAKFilename)

            # Copy/Send Files
            logger.info("Copy/Send File")
            shutil.copyfile(localPath, BAKFilePath)  # Create a local backup
            sftp.put(localPath, BAKFilePath)  # Copy the file to the target device

            # Cleanup old files
            logger.info("Cleanup old files")
            cleanup_old_files(copyDevice, bak_folder, BAKFilename)  # Remove old backups

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
