import pyautogui
import time
import sys
import argparse
from datetime import datetime, timedelta, date
import ctypes
import win32gui
import win32con
import win32process
import traceback


def getJitter(jitter=15):
    # use a hash of the current day to recalculate the jitter every day in a deterministic way
    # this does not need to be secure or perfectly random.
    h = hash(date.today().strftime("%Y-%m-%d"))

    if h < 0:
        return h % -jitter
    else:
        return h % jitter


def disableScreenLock():
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    PREVENT_SLEEP = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED

    if ctypes.windll.kernel32.SetThreadExecutionState(PREVENT_SLEEP):
        print("screen lock disabled")
        return True

    print("failed to disable screen lock")


def isWindowMaximized(hwnd):
    placement = win32gui.GetWindowPlacement(hwnd)
    return placement[1] == win32con.SW_SHOWMAXIMIZED


def isWindowForeground(hwnd):
    return win32gui.GetForegroundWindow() == hwnd


def getTeamsWindow():
    windows = []

    def enumWindowsCallback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            windowText = win32gui.GetWindowText(hwnd)
            className = win32gui.GetClassName(hwnd)

            if windowText.lower().endswith("microsoft teams"):
                windows.append((hwnd, windowText))
        return True

    win32gui.EnumWindows(enumWindowsCallback, windows)

    if len(windows) > 0:
        return windows[0][0]

    return None


def alternateSetForegroundWindow(teamsHwnd):
    # Method 2: Alternative approach if SetForegroundWindow fails
    print("Direct method failed, trying alternative approach...")

    try:
        # Get current foreground window's thread
        currentHwnd = win32gui.GetForegroundWindow()
        current_thread_id = win32process.GetWindowThreadProcessId(currentHwnd)[0]
        target_thread_id = win32process.GetWindowThreadProcessId(teamsHwnd)[0]

        # Attach input processing mechanism of the two threads
        if (
            current_thread_id != target_thread_id
            and current_thread_id != 0
            and target_thread_id != 0
        ):
            win32process.AttachThreadInput(current_thread_id, target_thread_id, True)

        # Show and set foreground
        win32gui.ShowWindow(teamsHwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(teamsHwnd)

        # Detach the input processing mechanism
        if current_thread_id != target_thread_id:
            win32process.AttachThreadInput(current_thread_id, target_thread_id, False)
        print("Alternative method completed")
    except Exception as e:
        print(f"Alternative method failed: {e}")
        traceback.print_exc()
        raise e


def setForegroundWindow(teamsHwnd):
    result = False
    # Method 1: Try SetForegroundWindow directly. Fails sometimes due to windows security preventing excessive botting (teams task bar icon flashes red when this happens)
    try:
        result = win32gui.SetForegroundWindow(teamsHwnd)
    except Exception as e:
        print(f"SetForegroundWindow failed: {e}")
        result = False
    if not result:
        alternateSetForegroundWindow(teamsHwnd)


def bringTeamsToFront():
    try:
        teamsHwnd = getTeamsWindow()

        if not teamsHwnd:
            return False

        window_title = win32gui.GetWindowText(teamsHwnd)

        # Check current state
        is_foreground = isWindowForeground(teamsHwnd)
        is_maximized = isWindowMaximized(teamsHwnd)

        # Restore window if it's minimized
        if win32gui.IsIconic(teamsHwnd):
            print("Teams Window is minimized, restoring...")
            win32gui.ShowWindow(teamsHwnd, win32con.SW_RESTORE)
            time.sleep(0.1)  # Small delay to let window restore

        # Maximize window if not already maximized
        if not is_maximized:
            print("Maximizing Teams window...")
            win32gui.ShowWindow(teamsHwnd, win32con.SW_MAXIMIZE)
            time.sleep(0.1)

        # Bring to front and give focus if not already in foreground
        if not is_foreground:
            print("Bringing Teams window to front and giving focus...")
            setForegroundWindow(teamsHwnd)
        time.sleep(0.2)

        if isWindowForeground(teamsHwnd) and isWindowMaximized(teamsHwnd):
            return True
        else:
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


class MouseMover:
    def __init__(
        self,
        checkInterval=30,
        moveInterval=300,
        startTime="08:00",
        endTime="16:00",
        jitter=15,
    ):
        self.checkInterval = checkInterval
        self.moveInterval = moveInterval
        self.startTime = startTime
        self.endTime = endTime
        self.jitter = jitter
        self.lastPosition = pyautogui.position()
        self.lastActivityTime = datetime.now()

        self.startHour, self.start_min = map(int, self.startTime.split(":"))
        self.endHour, self.end_min = map(int, self.endTime.split(":"))
        self.lastJitter = None
        self.active = False

        # Prevent pyautogui from raising exception when mouse is moved to corner
        pyautogui.FAILSAFE = True

    def logJitter(self):
        currentJitter = getJitter(self.jitter)
        if self.lastJitter is None or currentJitter != self.lastJitter:
            self.lastJitter = currentJitter

            if currentJitter == -1 or currentJitter == 1:
                minutes = "minute"
            else:
                minutes = "minutes"

            print(
                "Current jitter set to %d %s, active between %s and %s"
                % (currentJitter, minutes, self.getStartTime(), self.getEndTime())
            )

    def getStartTime(self):
        return (
            datetime.now().replace(
                hour=self.startHour, minute=self.start_min, second=0, microsecond=0
            )
            + timedelta(minutes=getJitter(self.jitter))
        ).time()

    def getEndTime(self):
        return (
            datetime.now().replace(
                hour=self.endHour, minute=self.end_min, second=0, microsecond=0
            )
            + timedelta(minutes=getJitter(self.jitter))
        ).time()

    def isActiveTime(self):
        now = datetime.now().time()

        startTime = self.getStartTime()
        endTime = self.getEndTime()

        # Handle case where end time is next day (e.g., 22:00 to 06:00)
        if startTime <= endTime:
            return startTime <= now <= endTime
        else:
            return now >= startTime or now <= endTime

    def detectActivity(self):
        current_position = pyautogui.position()
        if current_position != self.lastPosition:
            self.lastPosition = current_position
            self.lastActivityTime = datetime.now()
            return True
        return False

    def nudgeMouse(self):
        current_pos = pyautogui.position()

        # Move mouse slightly, then move back to original position
        for i in range(10):
            pyautogui.moveRel(1, 0, duration=0.1)
            time.sleep(0.01)

        for i in range(10):
            pyautogui.moveRel(-1, 0, duration=0.1)
            time.sleep(0.01)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Mouse moved")

    def start(self):
        print(
            f"Mouse Mover started - active between {self.startTime} and {self.endTime} with {self.jitter} minutes of random jitter"
        )
        print(
            f"Checking every {self.checkInterval}s, moving after {self.moveInterval}s of inactivity"
        )
        self.logJitter()
        print("Press Ctrl+C to stop")

        last_check_time = 0

        while True:
            try:
                # check if desired interval has elapsed. We do it in this way so we can quit the application quickly without waiting on a long wait for self.check_interval
                if time.time() - last_check_time < self.checkInterval:
                    time.sleep(1)
                    continue

                last_check_time = time.time()

                # skip if outside of the active time window
                if not self.isActiveTime():
                    current_time = datetime.now().strftime("%H:%M:%S")
                    if self.active:
                        self.active = False
                        startTime = self.getStartTime()
                        endTime = self.getEndTime()
                        print(
                            f"[{current_time}] Outside active hours ({startTime}-{endTime}), mouse mover paused"
                        )

                    time.sleep(self.checkInterval)
                    continue
                elif not self.active:
                    current_time = datetime.now().strftime("%H:%M:%S")
                    self.active = True
                    startTime = self.getStartTime()
                    endTime = self.getEndTime()
                    print(f"[{current_time}] Activating ({startTime}-{endTime})")

                # Check for user activity
                activity_detected = self.detectActivity()

                if activity_detected:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] User activity detected"
                    )

                # Calculate time since last activity
                time_since_activity = datetime.now() - self.lastActivityTime

                # If no activity for the specified interval, move mouse
                if time_since_activity.total_seconds() >= self.moveInterval:
                    bringTeamsToFront()
                    self.nudgeMouse()
                    self.lastActivityTime = datetime.now()  # Reset timer

                time.sleep(self.checkInterval)
                self.logJitter()  # log jitter when it changes at midnight

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Prevent screensaver by moving mouse during periods of inactivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bsc.py --jitter 0                              # Default: 8am-4pm, check every 30s, move after 5min, no jitter
  python bsc.py --start 09:00 --end 17:00 --jitter 0    # Active 9am-5pm, no jitter
  python bsc.py --start 09:00 --end 17:00 --jitter 15   # Active from randomly between 8:45am - 9:15am and 4:45pm and 5:15 pm (15 minutes of jitter)
  python bsc.py --check 60 --move 600                   # Check every minute, move mouse after 10min
        """,
    )

    parser.add_argument(
        "--check",
        "--check-interval",
        type=int,
        default=30,
        help="How often to check for inactivity in seconds (default: 30)",
    )
    parser.add_argument(
        "--move",
        "--move-interval",
        type=int,
        default=60,
        help="How long to wait before moving mouse in seconds (default: 60 = 1 minutes)",
    )
    parser.add_argument(
        "--start",
        "--start-time",
        type=str,
        default="08:00",
        help="Start time for active period in HH:MM format (default: 08:00)",
    )
    parser.add_argument(
        "--end",
        "--end-time",
        type=str,
        default="16:00",
        help="End time for active period in HH:MM format (default: 16:00)",
    )
    parser.add_argument(
        "--jitter",
        "--jitter",
        type=int,
        default=15,
        help="Amount of random jitter (in minutes) to add to or remove from the start and end times",
    )

    return parser.parse_args()


def isTimeFormatValid(time_str):
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def main():
    args = parse_arguments()

    if not isTimeFormatValid(args.start):
        print(
            f"Error: Invalid start time format '{args.start}'. Use HH:MM format (e.g., 08:00)"
        )
        sys.exit(1)

    if not isTimeFormatValid(args.end):
        print(
            f"Error: Invalid end time format '{args.end}'. Use HH:MM format (e.g., 16:00)"
        )
        sys.exit(1)

    if args.check <= 0:
        print(f"Error: Check interval must be positive, got {args.check}")
        sys.exit(1)

    if args.move <= 0:
        print(f"Error: Move interval must be positive, got {args.move}")
        sys.exit(1)

    try:
        # Disable screen lock
        disableScreenLock()

        # Create and start mouse mover with command line arguments
        mover = MouseMover(
            checkInterval=args.check,
            moveInterval=args.move,
            startTime=args.start,
            endTime=args.end,
            jitter=args.jitter,
        )
        mover.start()

    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
