from pathlib import Path
from typing import List, Tuple

from lxml import etree

from download_data import get_file_names


def extract_time_hr_pairs(tcx_path: Path) -> List[Tuple[str, int]]:
    """
    Extract (timestamp, heart_rate) pairs from a TCX file.

    Parameters
    ----------
    tcx_path : Path
        Path to the TCX XML file.

    Returns
    -------
    List[Tuple[str, int]]
        List of (timestamp, heart_rate) pairs.
        Timestamp is returned as an ISO8601 string.
    """
    root = etree.parse(tcx_path)

    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

    trackpoints = root.findall(".//tcx:Trackpoint", namespaces=ns)

    results: List[Tuple[str, int]] = []

    for tp in trackpoints:
        time_el = tp.find("tcx:Time", namespaces=ns)
        hr_el = tp.find("tcx:HeartRateBpm/tcx:Value", namespaces=ns)

        # Only include points with both time and heart rate
        if time_el is not None and hr_el is not None:
            try:
                hr = int(hr_el.text)
                results.append((time_el.text, hr))
            except (TypeError, ValueError):
                continue

    return results


def calculate_low_hr_percentage(time_hr_pairs: List[Tuple[str, int]]) -> float:
    count = len(time_hr_pairs)
    under_160 = 0
    for time, hr in time_hr_pairs:
        if hr <= 160:
            under_160 += 1
        count += 1
    return under_160 / count


if __name__ == "__main__":
    files = get_file_names()
    all_hrs: List[Tuple[str, int]] = []
    for file in files:
        all_hrs = all_hrs + extract_time_hr_pairs(Path("data", file))
    print(f"{calculate_low_hr_percentage(all_hrs):.3f}")
