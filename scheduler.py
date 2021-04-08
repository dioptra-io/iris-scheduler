import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests

IRIS_URL = "https://iris.dioptra.io/api"


def request(method, path, **kwargs):
    req = requests.request(method, IRIS_URL + path, **kwargs)
    req.raise_for_status()
    return req.json()


def start_time(measurement):
    return datetime.fromisoformat(measurement["start_time"])


def should_schedule(freq, last_measurement):
    if not last_measurement:
        return True
    diff = datetime.now() - start_time(last_measurement)
    if freq == "hourly":
        if diff >= timedelta(hours=1):
            return True
    if freq == "daily":
        if diff >= timedelta(days=1):
            return True
    if freq == "weekly":
        if diff >= timedelta(weeks=1):
            return True
    return False


def main():
    logging.basicConfig(level=logging.INFO)

    logging.info("Authenticating...")
    data = {
        "username": os.environ["IRIS_USERNAME"],
        "password": os.environ["IRIS_PASSWORD"],
    }
    res = request("POST", "/profile/token", data=data)
    headers = {"Authorization": f"Bearer {res['access_token']}"}

    logging.info("Uploading target lists...")
    for file in Path("targets").glob("*.txt"):
        logging.info(f"Processing {file}...")
        with file.open("rb") as f:
            request("POST", "/targets/", files={"targets_file": f}, headers=headers)

    for freq in ("oneshot", "hourly", "daily", "weekly"):
        for file in Path(freq).glob("*.json"):
            logging.info(f"Processing {file}...")
            measurement = json.loads(file.read_text())
            measurement.setdefault("tags", [])
            measurement["tags"].append(file.name)

            res = request(
                "GET",
                "/measurements/",
                params={"limit": 200, "tag": file.name},
                headers=headers,
            )

            last = None
            if res["count"] > 0:
                last = sorted(res["results"], key=start_time)[-1]
            if should_schedule(freq, last):
                logging.info("Scheduling measurement...")
                request("POST", "/measurements/", json=measurement, headers=headers)
            else:
                logging.info("Measurement already scheduled")


if __name__ == "__main__":
    main()
