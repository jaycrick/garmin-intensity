"""🏃‍♂️ Comprehensive Garmin Connect API Demo.
==========================================

This is a comprehensive demonstration program showing ALL available API calls
and error handling patterns for python-garminconnect.

For a simple getting-started example, see example.py

Dependencies:
pip3 install garth requests readchar

Environment Variables (optional):
export EMAIL=<your garmin email address>
export PASSWORD=<your garmin password>
export GARMINTOKENS=<path to token storage>
"""

import datetime
import json
import logging
import os
import sys
from contextlib import suppress
from datetime import timedelta
from getpass import getpass
from pathlib import Path
from typing import Any
from .auth import init_api

import readchar
import requests
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garth.exc import GarthException, GarthHTTPError


class Config:
    """Configuration class for the Garmin Connect API demo."""

    def __init__(self):
        # Load environment variables
        self.email = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
        self.tokenstore_base64 = (
            os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
        )

        # Date settings
        self.today = datetime.date.today()
        self.week_start = self.today - timedelta(days=7)
        self.month_start = self.today - timedelta(days=30)

        # API call settings
        self.default_limit = 100
        self.start = 0
        self.start_badge = 1  # Badge related calls start counting at 1

        # Activity settings
        self.activitytype = ""  # Possible values: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
        self.activityfile = "test_data/*.gpx"  # Supported file types: .fit .gpx .tcx
        self.workoutfile = "test_data/sample_workout.json"  # Sample workout JSON file

        # Export settings
        self.export_dir = Path("your_data")
        self.export_dir.mkdir(exist_ok=True)


# Initialize configuration
config = Config()


def download_activities_by_date(api: Garmin) -> None:
    """Download activities by date range in multiple formats."""
    try:
        print(
            f"📥 Downloading activities by date range ({config.week_start.isoformat()} to {config.today.isoformat()})..."
        )

        activities = api.get_activities_by_date(
            config.week_start.isoformat(), config.today.isoformat()
        )

        if not activities:
            print("ℹ️ No activities found in the specified date range")
            return

        print(f"📊 Found {len(activities)} activities to download")

        for activity in activities:
            activity_id = activity.get("activityId")
            activity_name = activity.get("activityName", "Unknown")
            start_time = (
                activity.get("startTimeLocal", "").replace(":", "-").replace(" ", "_")
            )

            if not activity_id:
                continue

            print(f"📥 Downloading: {activity_name} (ID: {activity_id})")

            # Formats to download
            formats = ["FIT", "GPX", "TCX", "ORIGINAL", "CSV"]

            for fmt in formats:
                try:
                    if fmt == "ORIGINAL":
                        filename = f"{start_time}_{activity_id}_ACTIVITY.zip"
                    elif fmt == "CSV":
                        filename = f"{start_time}_{activity_id}_ACTIVITY.json"
                    else:
                        filename = f"{start_time}_{activity_id}_ACTIVITY.{fmt.lower()}"

                    filepath = config.export_dir / filename

                    if filepath.exists():
                        continue

                    if fmt == "CSV":
                        activity_details = api.get_activity_details(activity_id)
                        with open(filepath, "w", encoding="utf-8") as f:
                            import json

                            json.dump(activity_details, f, indent=2, ensure_ascii=False)
                        print(f"  ✅ {fmt}: {filename}")

                    else:
                        # String-based format (portable across versions)
                        content = api.download_activity(activity_id, dl_fmt=fmt)

                        if content:
                            with open(filepath, "wb") as f:
                                f.write(content)
                            print(f"  ✅ {fmt}: {filename}")
                        else:
                            print(f"  ❌ {fmt}: No content available")

                except Exception as e:
                    print(f"  ❌ {fmt}: Error downloading - {e}")

        print(f"✅ Activity downloads completed! Files saved to: {config.export_dir}")

    except Exception as e:
        print(f"❌ Error downloading activities: {e}")


def download_all_activities(api: Garmin) -> None:
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
                    content = api.download_activity(activity_id, dl_fmt="FIT")
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
    """Main program loop with funny health status in menu prompt."""
    # Display export directory information on startup
    print(f"📁 Exported data will be saved to the directory: '{config.export_dir}'")
    print("📄 All API responses are written to: 'response.json'")

    api_instance = init_api(config.email, config.password)
    current_category = None

    while True:
        try:
            if api_instance:
                # Add health status in menu prompt
                try:
                    summary = api_instance.get_user_summary(config.today.isoformat())
                    hydration_data = None
                    with suppress(Exception):
                        hydration_data = api_instance.get_hydration_data(
                            config.today.isoformat()
                        )

                    if summary:
                        steps = summary.get("totalSteps") or 0
                        calories = summary.get("totalKilocalories") or 0

                        # Build stats string with hydration if available
                        stats_parts = [f"{steps:,} steps", f"{calories} kcal"]

                        if hydration_data and hydration_data.get("valueInML"):
                            hydration_ml = int(hydration_data.get("valueInML", 0))
                            hydration_cups = round(hydration_ml / 240, 1)
                            hydration_goal = hydration_data.get("goalInML", 0)

                            if hydration_goal > 0:
                                hydration_percent = round(
                                    (hydration_ml / hydration_goal) * 100
                                )
                                stats_parts.append(
                                    f"{hydration_ml}ml water ({hydration_percent}% of goal)"
                                )
                            else:
                                stats_parts.append(
                                    f"{hydration_ml}ml water ({hydration_cups} cups)"
                                )

                        stats_string = " | ".join(stats_parts)
                        print(f"\n📊 Your Stats Today: {stats_string}")

                        if steps < 5000:
                            print("🐌 Time to get those legs moving!")
                        elif steps > 15000:
                            print("🏃‍♂️ You're crushing it today!")
                        else:
                            print("👍 Nice progress! Keep it up!")
                except Exception as e:
                    print(
                        f"Unable to fetch stats for display: {e}"
                    )  # Silently skip if stats can't be fetched

            # Display appropriate menu
            if current_category is None:
                print_main_menu()
                option = safe_readkey()

                # Handle main menu options
                if option == "q":
                    print(
                        "Be active, generate some data to play with next time ;-) Bye!"
                    )
                    break
                if option in menu_categories:
                    current_category = option
                else:
                    print(
                        f"❌ Invalid selection. Use {', '.join(menu_categories.keys())} for categories or 'q' to quit"
                    )
            else:
                # In a category - show category menu
                print_category_menu(current_category)
                option = safe_readkey()

                # Handle category menu options
                if option == "q":
                    current_category = None  # Back to main menu
                elif option in "0123456789abcdefghijklmnopqrstuvwxyz":
                    try:
                        category_data = menu_categories[current_category]
                        category_options = category_data["options"]
                        if option in category_options:
                            api_key = category_options[option]["key"]
                            execute_api_call(api_instance, api_key)
                        else:
                            valid_keys = ", ".join(category_options.keys())
                            print(
                                f"❌ Invalid option selection. Valid options: {valid_keys}"
                            )
                    except Exception as e:
                        print(f"❌ Error processing option {option}: {e}")
                else:
                    print(
                        "❌ Invalid selection. Use numbers/letters for options or 'q' to go back/quit"
                    )

        except KeyboardInterrupt:
            print("\nInterrupted by user. Press q to quit.")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    config = Config()
    api_instance = init_api(config.email, config.password)
