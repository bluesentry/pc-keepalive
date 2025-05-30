# BSC Mouse Jiggler

## Purpose
This application periodically jiggles your mouse to prevent system inactivity and keeps your status as "Online" in Microsoft Teams.

While this program is running, your PC will not auto-lock or trigger the screensaver.

---

## Installation
Ensure Python 3.0+ is installed, then run:

    pip install -r requirements.txt

---

## Usage

    usage: bsc.py [-h] [--check CHECK] [--move MOVE] [--start START] [--end END]

    Prevent screensaver by moving the mouse during periods of inactivity.

    Options:
      -h, --help                  Show this help message and exit
      --check CHECK              How often to check for inactivity (seconds) [default: 30]
      --move MOVE                How long to wait before moving mouse (seconds) [default: 60]
      --start START              Start time for active period in HH:MM [default: 08:00]
      --end END                  End time for active period in HH:MM [default: 16:00]

---

## Examples

    python bsc.py
        # Default settings: 8 AM - 4 PM, check every 30 seconds, move mouse after 1 minute

    python bsc.py --start 09:00 --end 17:00
        # Active period set from 9 AM to 5 PM

    python bsc.py --check 60 --move 600
        # Check every 1 minute, move mouse after 10 minutes of inactivity
