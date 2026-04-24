"""Stream-parse Apple Health export.xml and return aggregated daily data.

Designed for the standard Apple Health XML export (HealthKit Export Version 14).
Streams through the XML to avoid loading 200+ MB into memory at once.
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

_DATETIME_FMT = "%Y-%m-%d %H:%M:%S %z"

# All "asleep" state values across iOS versions
_SLEEP_ASLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepDeep",
    "HKCategoryValueSleepAnalysisAsleepREM",
    "HKCategoryValueSleepAnalysisAsleep",  # pre-iOS 16
}

# Workout type → intensity bucket
_HIGH_INTENSITY = {"Running", "HIIT", "CrossTraining", "JumpRope", "StepTraining", "Cycling", "Swimming"}
_LOW_INTENSITY = {"Walking", "Stairs"}


def _find_export_zip() -> Path | None:
    """Walk up from this file's directory until export.zip is found."""
    search = Path(__file__).resolve().parent
    for _ in range(8):
        candidate = search / "export.zip"
        if candidate.exists():
            return candidate
        search = search.parent
    return None


def parse_apple_health_export(zip_path: str | None = None, days: int = 30) -> dict:
    """
    Stream-parse an Apple Health export.zip and return aggregated daily data
    for the last ``days`` days (inclusive of today).

    Returns:
        daily_steps         {date_str: int}
        daily_workouts      {date_str: [{type, duration_min, energy_kcal}]}
        daily_active_energy {date_str: float kcal}
        daily_sleep         {date_str: float hrs}
        date_range_start    str (ISO date)
        date_range_end      str (ISO date, today)
        totals              summary aggregates dict
    """
    if zip_path is None:
        found = _find_export_zip()
        if found is None:
            raise FileNotFoundError(
                "export.zip not found. Place the Apple Health export archive in the project root."
            )
        zip_path = str(found)

    today = date.today()
    cutoff = (today - timedelta(days=days - 1)).isoformat()

    daily_steps: dict[str, float] = defaultdict(float)
    daily_active_energy: dict[str, float] = defaultdict(float)
    daily_sleep: dict[str, float] = defaultdict(float)
    daily_workouts: dict[str, list] = defaultdict(list)

    with zipfile.ZipFile(zip_path, "r") as z:
        with z.open("apple_health_export/export.xml") as f:
            for _event, elem in ET.iterparse(f, events=["start"]):
                if elem.tag == "Record":
                    t = elem.get("type", "")
                    start_date_str = elem.get("startDate", "")[:10]

                    if start_date_str >= cutoff:
                        raw_val = elem.get("value") or "0"
                        try:
                            val = float(raw_val)
                        except ValueError:
                            val = 0.0

                        if t == "HKQuantityTypeIdentifierStepCount":
                            daily_steps[start_date_str] += val

                        elif t == "HKQuantityTypeIdentifierActiveEnergyBurned":
                            daily_active_energy[start_date_str] += val

                        elif t == "HKCategoryTypeIdentifierSleepAnalysis":
                            sleep_val = elem.get("value", "")
                            if sleep_val in _SLEEP_ASLEEP_VALUES:
                                end_str = elem.get("endDate", "")
                                start_str = elem.get("startDate", "")
                                if end_str and start_str:
                                    try:
                                        s_dt = datetime.strptime(start_str, _DATETIME_FMT)
                                        e_dt = datetime.strptime(end_str, _DATETIME_FMT)
                                        dur = (e_dt - s_dt).total_seconds() / 3600
                                        # Attribute to the morning (end date)
                                        night = e_dt.date().isoformat()
                                        if night >= cutoff:
                                            daily_sleep[night] += dur
                                    except Exception:
                                        pass

                    elem.clear()

                elif elem.tag == "Workout":
                    start_date_str = elem.get("startDate", "")[:10]
                    if start_date_str >= cutoff:
                        w_type = elem.get("workoutActivityType", "").replace(
                            "HKWorkoutActivityType", ""
                        )
                        duration = float(elem.get("duration") or 0)
                        energy = float(elem.get("totalEnergyBurned") or 0)
                        if duration > 0:
                            daily_workouts[start_date_str].append({
                                "type": w_type,
                                "duration_min": round(duration, 1),
                                "energy_kcal": round(energy),
                            })
                    elem.clear()

    # Build sorted regular dicts
    steps_dict = {k: int(v) for k, v in sorted(daily_steps.items())}
    workouts_dict = dict(sorted(daily_workouts.items()))
    energy_dict = {k: round(v, 1) for k, v in sorted(daily_active_energy.items())}
    sleep_dict = {k: round(v, 2) for k, v in sorted(daily_sleep.items())}

    # Compute summary totals
    total_steps_30d = sum(steps_dict.values())
    num_days_with_steps = max(len(steps_dict), 1)
    start_7d = (today - timedelta(days=6)).isoformat()

    total_steps_7d = sum(v for k, v in steps_dict.items() if k >= start_7d)
    all_sessions_30d = [s for ss in workouts_dict.values() for s in ss]
    sessions_7d = [
        s for d, ss in workouts_dict.items() if d >= start_7d for s in ss
    ]
    total_duration_30d = sum(s["duration_min"] for s in all_sessions_30d)
    total_duration_7d = sum(s["duration_min"] for s in sessions_7d)

    type_counts = dict(Counter(s["type"] for s in all_sessions_30d).most_common())

    totals = {
        "total_steps_30d": total_steps_30d,
        "total_steps_7d": total_steps_7d,
        "avg_daily_steps": round(total_steps_30d / num_days_with_steps) if total_steps_30d else 0,
        "avg_daily_steps_7d": round(total_steps_7d / 7) if total_steps_7d else 0,
        "total_workout_sessions_30d": len(all_sessions_30d),
        "total_workout_sessions_7d": len(sessions_7d),
        "avg_workout_min_per_session": (
            round(total_duration_30d / len(all_sessions_30d), 1) if all_sessions_30d else 0
        ),
        "avg_workout_min_7d": round(total_duration_7d / 7, 1),
        "avg_workout_min_30d": round(total_duration_30d / 30, 1),
        "workout_type_counts": type_counts,
    }

    return {
        "daily_steps": steps_dict,
        "daily_workouts": workouts_dict,
        "daily_active_energy": energy_dict,
        "daily_sleep": sleep_dict,
        "date_range_start": cutoff,
        "date_range_end": today.isoformat(),
        "totals": totals,
    }
