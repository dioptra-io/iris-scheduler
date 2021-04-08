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


def main():
    logging.basicConfig(level=logging.INFO)

    logging.info("Authenticating...")
    data = {
        "username": os.environ["IRIS_USERNAME"],
        "password": os.environ["IRIS_PASSWORD"],
    }
    res = request("POST", "/profile/token", data=data)
    headers = {"Authorization": f"Bearer {res['access_token']}"}

    logging.info("Uploading targets lists...")
    for file in Path("targets").glob("*.txt"):
        logging.info(f"Processing {file}...")
        with file.open("rb") as f:
            request("POST", "/targets/", files={"targets_file": f}, headers=headers)

    for file in Path("daily").glob("*.json"):
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

        if res["count"] == 0:
            logging.info("Measurement not found, scheduling...")
            request("POST", "/measurements/", json=measurement, headers=headers)
        else:
            last = sorted(res["results"], key=start_time)[-1]
            if datetime.now() - start_time(last) > timedelta(days=1):
                logging.info("Measurement too old, scheduling...")
                request("POST", "/measurements/", json=measurement, headers=headers)
            else:
                logging.info("Measurement already scheduled")


if __name__ == "__main__":
    main()
