# iris-scheduled

[![Scheduler](https://github.com/dioptra-io/iris-scheduled/actions/workflows/scheduler.yml/badge.svg)](https://github.com/dioptra-io/iris-scheduled/actions/workflows/scheduler.yml)

[`MEASUREMENTS.md`](MEASUREMENTS.md)

The [`scheduler.py`](scheduler.py) script is run every hour (:00) and on new commits via the [`scheduler.yml`](.github/workflows/scheduler.yml) workflow.
It acts as follows:
- Target lists in `targets/` are automatically uploaded.
- Measurements are tagged with their filename.
- Measurements in `oneshot/` are created only once.
- Measurements in `hourly/` are created every hour.
- Measurements in `daily/` are created once a day.
- Measurements in `weekly/` are created once a week, on Friday.
