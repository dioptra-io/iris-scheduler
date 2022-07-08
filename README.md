# iris-scheduler

[![Scheduler](https://github.com/dioptra-io/iris-scheduler/actions/workflows/scheduler.yml/badge.svg)](https://github.com/dioptra-io/iris-scheduler/actions/workflows/scheduler.yml)

[`MEASUREMENTS.md`](MEASUREMENTS.md)

The [`iris-scheduler`](/iris_scheduler/main.py) script is run every fifteen minutes and on new commits via the [`scheduler.yml`](.github/workflows/scheduler.yml) workflow.

Each measurement file must have the following metadata:
```js
{
  // ...,
  "scheduler": {
    "cron": "0 0 * * Sat",
    "not_before": "2022-06-30T00:00:00",
    // Optional, to stop scheduling the measurement after some time.
    "not_after": "2030-01-01T00:00:00",
    "type": "regular" // or "zeph"
  }
}
```
