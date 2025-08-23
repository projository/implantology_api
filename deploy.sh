#!/bin/bash

# Navigate to the project directory
cd /home/ubuntu/api

# Pull the latest changes
git pull origin main

# Activate virtualenv
source env/bin/activate

# Install the latest dependencies
pip install -r requirements.txt

# Deactivate virtualenv
deactivate

# Restart the FastAPI service
sudo systemctl restart api

# Print success message
echo "Application updated and restarted successfully!"
