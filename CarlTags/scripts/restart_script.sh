#!/bin/bash

# Define the Python script location
SCRIPT_PATH="scripts/updater.py"

while true; do
  echo "Restarting $SCRIPT_PATH..."
  
  # Kill existing instance if running
  pkill -f "$SCRIPT_PATH"
  
  # Start the Python script
  python "$SCRIPT_PATH" &
  
  echo "$SCRIPT_PATH restarted successfully."
  
  # Wait for 12 hours
  sleep 43200
done

# nohup ./scripts/restart_script.sh &

# pkill -f scripts/restart_script.sh
