from datetime import datetime, timezone
from pathlib import Path

from iris_client import IrisClient

from iris_scheduler.logger import logger


def get_last_modified(client: IrisClient, key: str) -> datetime | None:
    res = client.get(f"/targets/{key}", params={"with_content": False})
    if res.is_success:
        target_file = res.json()
        return datetime.fromisoformat(target_file["last_modified"]).replace(
            tzinfo=timezone.utc
        )
    return None


def upload_target(client: IrisClient, file: Path, dry_run: bool) -> None:
    remote_date = get_last_modified(client, file.name)
    local_date = datetime.fromtimestamp(file.stat().st_mtime, timezone.utc)
    logger.info(
        "file=%s local_date=%s remote_date=%s",
        file.name,
        local_date,
        remote_date,
    )
    if remote_date and remote_date >= local_date:
        logger.info("file=%s action=skip", file.name)
    else:
        logger.info("file=%s action=upload", file.name)
        if not dry_run:
            with file.open("rb") as f:
                client.post("/targets/", files={"target_file": f}).raise_for_status()
    return None
