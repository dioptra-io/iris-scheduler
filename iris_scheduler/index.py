from datetime import datetime, timedelta
from pathlib import Path

from iris_client import IrisClient
from jinja2 import Environment, PackageLoader, select_autoescape


def creation_time(measurement: dict) -> datetime | None:
    if s := measurement["creation_time"]:
        return datetime.fromisoformat(s).replace(microsecond=0)
    return None


def start_time(measurement: dict) -> datetime | None:
    if s := measurement["start_time"]:
        return datetime.fromisoformat(s).replace(microsecond=0)
    return None


def end_time(measurement: dict) -> datetime | None:
    if s := measurement["end_time"]:
        return datetime.fromisoformat(s).replace(microsecond=0)
    return None


def duration(measurement: dict) -> timedelta | None:
    st, et = start_time(measurement), end_time(measurement)
    if st and et:
        return et - st
    return None


def measurement_name(measurement: dict) -> str:
    name = "Unknown"
    for tag in measurement["tags"]:
        if tag.endswith(".json"):
            name = tag[:-5]
            break
    return name


def generate_md(measurements: list[dict]) -> str:
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
            "uuid": measurement["uuid"],
            "short_uuid": measurement["uuid"].split("-")[0],
            "tool": measurement["tool"],
            "state": measurement["state"],
            "short_state": measurement["state"][0].upper(),
            "agents": len(measurement["agents"]),
            "created": creation_time(measurement),
            "start": start_time(measurement),
            "end": end_time(measurement),
            "duration": duration(measurement),
        }
        for measurement in measurements
    ]
    template = env.get_template("MEASUREMENTS.md")
    return template.render(measurements=measurements)


def index_measurements(iris: IrisClient, scheduler_tag: str, destination: Path) -> None:
    measurements = iris.all(
        "/measurements/", params={"limit": 200, "tag": scheduler_tag}
    )
    destination.write_text(generate_md(measurements))
