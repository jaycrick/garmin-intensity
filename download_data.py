import time
from getpass import getpass
from pathlib import Path

import garminconnect
from garminconnect import (GarminConnectAuthenticationError,
                           GarminConnectConnectionError)

# -----------------------
# Configuration
# -----------------------

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

PAGE_SIZE = 100  # Garmin API max is typically 100
SLEEP_SECONDS = 0.2  # be polite to the API

# -----------------------
# Login (no credentials stored)
# -----------------------

email = input("Enter Garmin email: ")
password = getpass("Enter Garmin password: ")

try:
    garmin = garminconnect.Garmin(email, password)
    garmin.login()
except GarminConnectAuthenticationError:
    raise RuntimeError("Authentication failed")
except GarminConnectConnectionError:
    raise RuntimeError("Connection error")

print(f"Logged in as: {garmin.display_name}")

# -----------------------
# Download all activities
# -----------------------

start = 0
total_downloaded = 0

while True:
    activities = garmin.get_activities(start, PAGE_SIZE)
    if not activities:
        break

    for activity in activities:
        activity_id = activity["activityId"]
        activity_type = activity["activityType"]["typeKey"]
        start_time = activity["startTimeLocal"].replace(":", "").replace(" ", "_")

        outfile = DATA_DIR / f"{start_time}_{activity_type}_{activity_id}.fit"

        if outfile.exists():
            continue  # already downloaded

        try:
            data = garmin.download_activity(
                activity_id, dl_fmt=garminconnect.ActivityDownloadFormat.FIT
            )
            with open(outfile, "wb") as f:
                f.write(data)

            total_downloaded += 1
            print(f"Downloaded {outfile.name}")

            time.sleep(SLEEP_SECONDS)

        except Exception as e:
            print(f"Failed to download activity {activity_id}: {e}")

    start += PAGE_SIZE

print(f"Finished. Downloaded {total_downloaded} new activities.")
