"""
Downloading all activities
"""

import json
from pathlib import Path
from typing import Any, List, Set

import pandas as pd
from auth.app_auth import Config, init_api
from garminconnect import Garmin

config = Config()


def get_file_names(data_dir: str = config.export_dir) -> Set[str]:
    """
    Lists names of all files in the data directory.
    """
    p = Path(data_dir)
    return {item.name for item in p.iterdir() if item.is_file()}


def extract_ids_from_path(file_name: str) -> str:
    return file_name.split("_")[-1].split(".")[0]


def extract_ids_from_directory(data_dir=config.export_dir):
    file_names = get_file_names(data_dir)
    return {extract_ids_from_path(file_name) for file_name in file_names}


# def get_running_activities_list():


def get_hr_zones(api: Garmin):
    running_activities = api.get_activities(start=0, limit=100, activitytype="running")
    track_activities: List[Any] = []
    # api.get_activities(
    #     start=0, limit=1, activitytype="track_running"
    # )
    print(f"{len(running_activities)} runs and {len(track_activities)} track runs")
    all_activities_ids = {
        activity.get("activityId")
        for activity in running_activities  # + track_activities
    }
    flat_data = []

    for number, id in enumerate(all_activities_ids):
        hr_zones = api.get_activity_hr_in_timezones(id)
        for row in hr_zones:
            new_row = row.copy()
            new_row["activity_number"] = number
            flat_data.append(new_row)

    df = pd.DataFrame(flat_data)
    weekly_zones = df.groupby("zoneNumber")["secsInZone"].sum().reset_index()
    total_time = weekly_zones["secsInZone"].sum()
    weekly_zones["pctInZone"] = weekly_zones["secsInZone"] / total_time

    print(weekly_zones)


def download_all_new_activities(api: Garmin, force=False) -> None:
    """Download all new activities as FIT files.
    Setting force=True will download all files."""
    try:
        print("📥 Downloading all new activities...")

        export_dir = config.export_dir
        export_dir.mkdir(exist_ok=True)

        start = 0
        limit = 100
        total_downloaded = 0

        while True:
            activities = api.get_activities(start, limit)
            if not activities:
                break

            print(f"📊 Retrieved {len(activities)} activities")

            for activity in activities:
                activity_id = activity.get("activityId")
                activity_name = activity.get("activityName", "Unknown")
                start_time = (
                    activity.get("startTimeLocal", "")
                    .replace(":", "-")
                    .replace(" ", "_")
                )
                activity_type = activity.get("activityType", {}).get(
                    "typeKey", "unknown"
                )

                if not activity_id:
                    continue

                filename = f"{start_time}_{activity_type}_{activity_id}.json"
                filepath = export_dir / filename

                if not force and filepath.exists():
                    continue

                print(f"📥 Downloading: {activity_name} (ID: {activity_id})")

                try:
                    content = api.get_activity_details(activity_id)
                    if content:
                        # Write dictionary to JSON
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(content, f, indent=2, ensure_ascii=False)
                        total_downloaded += 1
                        print(f"  ✅ Saved: {filename}")
                    else:
                        print(f"  ❌ No content for activity {activity_id}")
                except Exception as e:
                    print(f"  ❌ Error saving activity {activity_id}: {e}")

            start += limit

        print(f"✅ Completed. Downloaded {total_downloaded} activities.")

    except Exception as e:
        print(f"❌ Error downloading activities: {e}")


def main():
    api_instance = init_api()
    download_all_new_activities(api_instance)


if __name__ == "__main__":
    api_instance = init_api()
    download_all_new_activities(api_instance)
    # get_hr_zones(api_instance)
