import logging
from pathlib import Path

import typer
from iris_client import IrisClient

from iris_scheduler.index import index_measurements
from iris_scheduler.schedule import schedule_measurement
from iris_scheduler.upload import upload_target

INDEX_FILE = Path("MEASUREMENTS.md")
MEASUREMENTS_DIR = Path("measurements")
TARGETS_DIR = Path("targets")
SCHEDULER_TAG = "scheduled"


app = typer.Typer()


@app.command()
def main(
    dry_run: bool = typer.Option(
        False,
        help="Do not upload targets or create measurements",
    ),
    iris_base_url: str = typer.Option(
        None,
        help="Iris API URL",
        metavar="BASE_URL",
    ),
    iris_username: str = typer.Option(
        None,
        help="Iris API username",
        metavar="USERNAME",
    ),
    iris_password: str = typer.Option(
        None,
        help="Iris API password",
        metavar="PASSWORD",
    ),
) -> None:
    logging.basicConfig(level=logging.INFO)
    with IrisClient(
        base_url=iris_base_url,
        username=iris_username,
        password=iris_password,
    ) as client:
        for file in TARGETS_DIR.glob("*.csv"):
            upload_target(client, file, dry_run)
        for file in MEASUREMENTS_DIR.glob("*.json"):
            schedule_measurement(client, file, SCHEDULER_TAG, dry_run)
        index_measurements(client, SCHEDULER_TAG, INDEX_FILE)
