#!/bin/bash

sudo mv /home/pi/RPiBackups/RPiBackups.service /etc/systemd/system/ && sudo systemctl daemon-reload
python3 -m pip install -r /home/pi/RPiBackups/requirements.txt --no-cache-dir
chmod +x -R /home/pi/RPiBackups/*
mkdir /home/pi/RPiBackups/bak/
