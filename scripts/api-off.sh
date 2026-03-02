#!/bin/bash
# Disable all API access by creating the kill switch file and reloading Nginx
set -e
sudo touch /home/clicknback/app/api_off
sudo systemctl reload nginx

echo "API access disabled (kill switch ON)."
