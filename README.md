# Purpose
This application will periodically jiggle your mouse to prevent inactivity, and ensures that you always show as online on Microsoft Teams.

Be aware that while this program is running, your PC will not auto-lock or activate the screensaver.

# Installation
Ensure pythong 3.0+ is installed and run:

```
pip install -r requirements.txt
```

# Usage
usage: bsc.py [-h] [--check CHECK] [--move MOVE] [--start START] [--end END]

Prevent screensaver by moving mouse during periods of inactivity

options:
  -h, --help            show this help message and exit
  --check, --check-interval CHECK
                        How often to check for inactivity in seconds (default: 30)
  --move, --move-interval MOVE
                        How long to wait before moving mouse in seconds (default: 60 = 1 minutes)
  --start, --start-time START
                        Start time for active period in HH:MM format (default: 08:00)
  --end, --end-time END
                        End time for active period in HH:MM format (default: 16:00)

Examples:
  python bsc.py                           # Default: 8am-4pm, check every 30s, move after 5min
  python bsc.py --start 09:00 --end 17:00  # Active 9am-5pm
  python bsc.py --check 60 --move 600      # Check every minute, move mouse after 10min