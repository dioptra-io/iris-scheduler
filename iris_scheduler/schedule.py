import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import orjson
from crontab import CronTab
from iris_client import IrisClient
from pych_client import ClickHouseClient
from zeph.main import run_zeph

from iris_scheduler.logger import logger


def get_last(iris: IrisClient, tag: str) -> dict | None:
    if measurements := iris.all("/measurements/", params={"limit": 200, "tag": tag}):
        measurements.sort(key=lambda x: datetime.fromisoformat(x["creation_time"]))
        return measurements[-1]  # type: ignore
    return None


def get_next_run(cron: CronTab, last_run: datetime) -> datetime:
    seconds = cron.next(last_run, default_utc=True)
    return last_run + timedelta(seconds=seconds)


def schedule_measurement(
    iris: IrisClient,
    prefixes_dir: Path,
    scheduler_tag: str,
    file: Path,
    dry_run: bool,
) -> None:
    measurement = json.loads(file.read_text())
    scheduler = measurement.pop("scheduler")
    tags = [file.name, scheduler_tag]
    cron = CronTab(scheduler["cron"])
    not_before = datetime.fromisoformat(scheduler["not_before"])
    not_after = None
    if "not_after" in scheduler:
        not_after = datetime.fromisoformat(scheduler["not_after"])
    last = get_last(iris, file.name)
    last_run = datetime.fromisoformat(last["creation_time"]) if last else not_before
    next_run = get_next_run(cron, last_run)
    logger.info(
        "file=%s not_before=%s not_after=%s last_run=%s next_run=%s",
        file.name,
        not_before,
        not_after,
        last_run,
        next_run,
    )
    now = datetime.utcnow()
    if (not_after and now > not_after) or next_run > now:
        logger.info("file=%s action=skip", file.name)
        return None
    if last and last["state"] not in ("finished", "canceled"):
        logger.info("file=%s action=skip-unfinished", file.name)
        return None
    match scheduler["type"]:
        case "regular":
            schedule_regular_measurement(
                iris,
                file.name,
                measurement,
                tags,
                dry_run,
            )
        case "zeph-test":
            schedule_zeph_measurement(
                iris,
                prefixes_dir,
                file.name,
                last,
                measurement,
                tags,
                dry_run,
            )
        case _:
            raise RuntimeError("Unsupported measurement type")
    return None


def schedule_regular_measurement(
    iris: IrisClient,
    name: str,
    measurement: dict,
    tags: list[str],
    dry_run: bool,
) -> None:
    logger.info("file=%s action=schedule-regular", name)
    measurement.setdefault("tags", [])
    measurement["tags"] += tags
    if not dry_run:
        iris.post("/measurements/", json=measurement, timeout=600).raise_for_status()
    return None


def schedule_zeph_measurement(
    iris: IrisClient,
    prefixes_dir: Path,
    name: str,
    last: dict | None,
    measurement: dict,
    tags: list[str],
    dry_run: bool,
) -> Any:
    logger.info("file=%s action=schedule-zeph", name)
    params = {}
    if last:
        params["measurement_uuid"] = last["uuid"]
    credentials = iris.get("/users/me/services", params=params).json()
    measurement.setdefault("measurement_tags", [])
    measurement["measurement_tags"] += tags
    universe = set()
    prefixes_file = prefixes_dir / measurement["prefixes_file"]
    with prefixes_file.open() as f:
        for line in f:
            if line.startswith("#"):
                continue
            line = line.strip()
            assert line.endswith("/24") or line.endswith("/64")
            universe.add(line)
    logger.info("file=%s distinct-prefixes=%s", name, len(universe))
    with ClickHouseClient(**credentials["clickhouse"]) as clickhouse:
        try:
            return run_zeph(
                iris=iris,
                clickhouse=clickhouse,
                ranker=measurement["ranker"],
                universe=universe,
                agent_tag=measurement["agent_tag"],
                measurement_tags=measurement["measurement_tags"],
                tool=measurement["tool"],
                protocol=measurement["protocol"],
                min_ttl=measurement["min_ttl"],
                max_ttl=measurement["max_ttl"],
                exploration_ratio=measurement["exploration_ratio"],
                previous_uuid=last["uuid"] if last else None,
                fixed_budget=10,
                dry_run=dry_run,
            )
        except orjson.JSONDecodeError as e:
            # TODO: Move this exception handling to Zeph.
            print(e.doc)  # type: ignore
            raise e
