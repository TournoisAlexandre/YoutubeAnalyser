# Setting up automated updates

This document explains how to configure automation to update YouTube channel data daily.

## Prerequisites

- Python 3.6 or higher installed
- All project dependencies installed (`pip install -r requirements.txt`)
- A `channels.txt` file containing the list of channels to monitor (one per line)

## Important files

- `channels.txt`: List of YouTube channels to monitor (one per line)
- `daily_update.py`: Script that executes the data update
- `update_logs.txt`: Log file generated during updates

## Setting up automation

### On Windows (Task Scheduler)

1. Open "Task Scheduler" from the Start menu
2. Click on "Create Basic Task..." in the Actions panel
3. Give the task a name (e.g., "YouTube Data Update")
4. Select "Daily" for frequency
5. Choose the time you want to run the update (e.g., 3:00 AM)
6. Select "Start a program"
7. In "Program/script", enter the path to Python (e.g., `C:\Python39\python.exe`)
8. In "Arguments", enter the full path to the `daily_update.py` script (e.g., `D:\Users\Aries\Documents\MimounEngine\YoutubeAnalyser\daily_update.py`)
9. In "Start in", enter the project directory (e.g., `D:\Users\Aries\Documents\MimounEngine\YoutubeAnalyser`)
10. Finish the wizard and the task will be created

### On Linux/Mac (Cron)

1. Open a terminal
2. Run `crontab -e` to edit the crontab file
3. Add the following line to run the script every day at 3 AM:
   ```
   0 3 * * * cd /path/to/YoutubeAnalyser && /usr/bin/python3 daily_update.py
   ```
4. Replace `/path/to/YoutubeAnalyser` with the full path to the project directory
5. Save and exit the editor

## Verifying operation

To verify that the automation is working correctly:

1. Manually run the `daily_update.py` script first
2. Check that the `update_logs.txt` file is created and contains information about the update
3. Verify that the data is correctly updated in the database

## Customization

- To modify the list of monitored channels, simply edit the `channels.txt` file
- To change the update frequency, adjust the configuration in Task Scheduler or crontab
- To modify the maximum number of videos retrieved per channel, edit the `max_results` parameter in the `update_channels_data()` function in the `main.py` file

## Troubleshooting

If automatic updates are not working:

1. Check the `update_logs.txt` file for any errors
2. Make sure the path to Python and the script are correct in the configuration
3. Verify that the user running the task has the necessary permissions
4. Ensure that the YouTube API key is valid and that quotas are not exceeded
