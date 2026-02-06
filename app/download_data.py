"""
Downloading all activities
"""

from auth.app_auth import init_api, Config
from garminconnect import Garmin
# from garth.exc import GarthException, GarthHTTPError

config = Config()


def download_all_activities(api: Garmin, force=False) -> None:
    """Download all activities as FIT files."""
    try:
        print("📥 Downloading all activities...")

        export_dir = config.export_dir
        export_dir.mkdir(exist_ok=True)

        start = 0
        limit = 100
        total_downloaded = 0

        while True:
            activities = api.get_activities(start, limit)
            if not activities:
                break

            print(f"📊 Retrieved {len(activities)} activities (offset {start})")

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

                if filepath.exists():
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
    download_all_activities(api_instance)


if __name__ == "__main__":
    main()
