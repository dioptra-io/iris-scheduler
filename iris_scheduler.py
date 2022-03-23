import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from iris_client import IrisClient
from jinja2 import Environment, PackageLoader, select_autoescape

ISOWEEKDAYS = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 7,
}

SCHEDULER_TAG = "scheduled"


def creation_time(measurement: dict) -> datetime | None:
    if s := measurement["creation_time"]:
        return datetime.fromisoformat(s).replace(microsecond=0)


def start_time(measurement: dict) -> datetime | None:
    if s := measurement["start_time"]:
        return datetime.fromisoformat(s).replace(microsecond=0)


def end_time(measurement: dict) -> datetime | None:
    if s := measurement["end_time"]:
        return datetime.fromisoformat(s).replace(microsecond=0)


def duration(measurement: dict) -> timedelta | None:
    st, et = start_time(measurement), end_time(measurement)
    if st and et:
        return et - st


def measurement_name(measurement: dict) -> str:
    name = "Unknown"
    for tag in measurement["tags"]:
        if tag.endswith(".json"):
            name = tag[:-5]
            break
    return name


def generate_md(measurements):
    env = Environment(
        loader=PackageLoader("iris_scheduler"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    measurements = sorted(
        measurements, key=lambda x: (measurement_name(x), creation_time(x))
    )
    measurements = [
        {
            "name": measurement_name(measurement),
            "uuid": measurement["uuid"].split("-")[0],
            "tool": measurement.get("tool"),
            "state": measurement.get("state"),
            "created": creation_time(measurement),
            "start": start_time(measurement),
            "end": end_time(measurement),
            "duration": duration(measurement),
        }
        for measurement in measurements
    ]
    template = env.get_template("MEASUREMENTS.md")
    return template.render(measurements=measurements)


def should_schedule(freq, last_measurement, meta):
    diff = None
    if last_measurement:
        diff = datetime.now() - start_time(last_measurement)
    logging.info("freq=%s diff=%s meta=%s", freq, diff, meta)
    if freq == "hourly":
        delta = 1
        if meta:
            delta = int(meta)
        if not last_measurement or diff >= timedelta(hours=delta):
            return True
    if freq == "daily":
        if not last_measurement or diff >= timedelta(days=1):
            return True
    if freq == "weekly":
        if datetime.now().isoweekday() == ISOWEEKDAYS[meta]:
            if not last_measurement or diff > timedelta(days=1):
                return True
    return False


def schedule_measurements(client: IrisClient) -> None:
    for freq in ("oneshot", "hourly", "daily", "weekly"):
        for file in Path(f"_{freq}").glob("*.json"):
            logging.info("Processing %s...", file)

            # Extract the optional meta component:
            # measurement.saturday.json => saturday
            meta = ""
            if len(str(file).split(".")) == 3:
                meta = str(file).split(".")[1].lower().strip()

            measurement = json.loads(file.read_text())
            measurement.setdefault("tags", [])
            measurement["tags"].append(file.name)
            measurement["tags"].append(SCHEDULER_TAG)

            measurements = client.all("/measurements/", params=dict(tag=file.name))
            if measurements:
                last = sorted(measurements, key=creation_time)[-1]
            else:
                last = None

            if should_schedule(freq, last, meta):
                logging.info("Scheduling measurement...")
                client.post("/measurements/", json=measurement)
            else:
                logging.info("Skipping measurement...")


def upload_target_lists(client: IrisClient) -> None:
    for file in Path("targets").glob("*.csv"):
        logging.info("Uploading %s...", file)
        with file.open("rb") as f:
            client.post("/targets/", files=dict(target_file=f))


def index_measurements(client: IrisClient, destination: Path) -> None:
    measurements = client.all("/measurements/", params=dict(tag=SCHEDULER_TAG))
    destination.write_text(generate_md(measurements))


def main():
    logging.basicConfig(level=logging.INFO)
    with IrisClient() as client:
        upload_target_lists(client)
        schedule_measurements(client)
        index_measurements(client, Path("MEASUREMENTS.md"))


if __name__ == "__main__":
    main()
