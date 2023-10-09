#!/bin/bash

sudo mv /home/pi/RPiBackups/RPiBackups.service /etc/systemd/system/ && sudo systemctl daemon-reload
python3 -m pip install paramiko --no-cache-dir
chmod +x -R /home/pi/RPiBackups/*
mkdir /home/pi/RPiBackups/bak/
