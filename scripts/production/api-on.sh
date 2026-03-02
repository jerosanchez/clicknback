#!/bin/bash
# Enable API access by removing the kill switch file and reloading Nginx
set -e
sudo rm -f /home/clicknback/app/api_off
sudo systemctl reload nginx

echo "API access enabled (kill switch OFF)."
