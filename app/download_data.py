"""
Downloading all activities
"""

from auth.app_auth import init_api, Config
from garminconnect import Garmin
from pathlib import Path
from typing import Set

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

                filename = f"{start_time}_{activity_type}_{activity_id}.fit"
                filepath = export_dir / filename

                if not force and filepath.exists():
                    continue

                print(f"📥 Downloading: {activity_name} (ID: {activity_id})")

                try:
                    content = api.download_activity(activity_id)
                    if content:
                        with open(filepath, "wb") as f:
                            f.write(content)
                        total_downloaded += 1
                        print(f"  ✅ Saved: {filename}")
                    else:
                        print(f"  ❌ No content for activity {activity_id}")

                except Exception as e:
                    print(f"  ❌ Error downloading {activity_id}: {e}")

            start += limit

        print(f"✅ Completed. Downloaded {total_downloaded} activities.")

    except Exception as e:
        print(f"❌ Error downloading activities: {e}")


def main():
    api_instance = init_api()
    download_all_new_activities(api_instance)


if __name__ == "__main__":
    main()
