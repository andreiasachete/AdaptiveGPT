#!/bin/bash
# This file should be placed at /usr/local/bin/adaptivegpt_activity_monitor.sh
# In addition, we must create a cron job to run this script every XX minutes (e.g., 2).
# To do so, first we run:
# crontab -e
# Then, we add the following line to the end of the file: */2 * * * * /usr/local/bin/adaptivegpt_activity_monitor.sh >> /home/fabiorossi/AdaptiveGPT/cronjob.log 2>&1

LOG_FILE="/home/fabiorossi/AdaptiveGPT/gunicorn_accesses.log"
IDLE_LIMIT=7200  # 2 hours in seconds

# If the log file exists
if [ -f "$LOG_FILE" ]; then
    # Gathering the current time (both in seconds since epoch and formatted)
    NOW=$(date +%s)
    CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")

    # Checking the last modification time
    LAST_MOD=$(stat -c %Y "$LOG_FILE")
    
    # Calculating the idle time (in seconds)
    IDLE_TIME=$((NOW - LAST_MOD))

    # Checking if the idle time is greater than or equal to the limit
    if [ $IDLE_TIME -ge $IDLE_LIMIT ]; then
        echo "[$CURRENT_TIME] Inactivity detected: > $((IDLE_TIME / 3600)) hours. Restarting Gunicorn..."
        systemctl restart adaptive.service
    else
        echo "[$CURRENT_TIME] Idle time is $((IDLE_TIME / 60)) minutes (limit is $((IDLE_LIMIT / 60)) minutes). No restart needed."
    fi
fi
