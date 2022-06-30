import json
from datetime import datetime, timedelta
from pathlib import Path

from crontab import CronTab
from iris_client import IrisClient

from iris_scheduler.logger import logger


def get_last_run(client: IrisClient, tag: str) -> datetime | None:
    if measurements := client.all("/measurements/", params={"limit": 200, "tag": tag}):
        return max(datetime.fromisoformat(m["creation_time"]) for m in measurements)
    return None


def get_next_run(cron: CronTab, last_run: datetime) -> datetime:
    seconds = cron.next(last_run, default_utc=True)
    return last_run + timedelta(seconds=seconds)


def schedule_measurement(
    client: IrisClient, file: Path, scheduler_tag: str, dry_run: bool
) -> None:
    measurement = json.loads(file.read_text())
    measurement.setdefault("tags", [])
    measurement["tags"] += [file.name, scheduler_tag]
    scheduler = measurement.pop("scheduler")
    cron = CronTab(scheduler["cron"])
    not_before = datetime.fromisoformat(scheduler["not_before"])
    not_after = None
    if "not_after" in scheduler:
        not_after = datetime.fromisoformat(scheduler["not_after"])
    last_run = get_last_run(client, "exhaustive.saturday.json")
    next_run = get_next_run(cron, last_run or not_before)
    logger.info(
        "file=%s not_before=%s not_after=%s last_run=%s next_run=%s",
        file.name,
        not_before,
        not_after,
        last_run,
        next_run,
    )
    if next_run > datetime.utcnow() or (not_after and next_run > not_after):
        logger.info("file=%s action=skip", file.name)
    else:
        logger.info("file=%s action=schedule", file.name)
        if not dry_run:
            client.post("/measurements/", json=measurement).raise_for_status()
    return None
