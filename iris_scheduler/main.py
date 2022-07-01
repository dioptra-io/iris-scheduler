import logging
from pathlib import Path

import httpx
import typer
from iris_client import IrisClient
from pych_client import ClickHouseClient

from iris_scheduler.index import index_measurements
from iris_scheduler.schedule import schedule_measurement
from iris_scheduler.upload import upload_target

INDEX_FILE = Path("MEASUREMENTS.md")
MEASUREMENTS_DIR = Path("measurements")
PREFIXES_DIR = Path("prefixes")
TARGETS_DIR = Path("targets")
SCHEDULER_TAG = "scheduled"


app = typer.Typer()


@app.command()
def main(
    dry_run: bool = typer.Option(
        False,
        help="Do not upload targets or create measurements",
    ),
    clickhouse_base_url: str = typer.Option(
        None,
        help="ClickHouse URL",
        metavar="URL",
    ),
    clickhouse_database: str = typer.Option(
        None,
        help="ClickHouse database",
        metavar="DATABASE",
    ),
    clickhouse_username: str = typer.Option(
        None,
        help="ClickHouse username",
        metavar="USERNAME",
    ),
    clickhouse_password: str = typer.Option(
        None,
        help="ClickHouse password",
        metavar="PASSWORD",
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
    with (
        IrisClient(
            base_url=iris_base_url,
            username=iris_username,
            password=iris_password,
            timeout=httpx.Timeout(5.0, read=None, write=None),
        ) as iris,
        ClickHouseClient(
            base_url=clickhouse_base_url,
            database=clickhouse_database,
            username=clickhouse_username,
            password=clickhouse_password,
        ) as clickhouse,
    ):
        for file in TARGETS_DIR.glob("*.csv"):
            upload_target(iris, file, dry_run)
        for file in MEASUREMENTS_DIR.glob("*.json"):
            schedule_measurement(
                iris, clickhouse, PREFIXES_DIR, SCHEDULER_TAG, file, dry_run
            )
        index_measurements(iris, SCHEDULER_TAG, INDEX_FILE)
