# 🧭 iris test-scheduler

This branch provides a **testing version of the Iris scheduler** used for safe experimentation and validation of measurement scheduling logic without impacting production systems.

## Key Differences from `main`

- **Tag:** Uses `SCHEDULER_TAG = "test"` to clearly identify test-scheduled measurements.
- **Measurement Type:** Runs the `"zeph-test"` measurement case instead of the production `"zeph"` case.
- **Fixed Budget:** Sets a small, constant probing budget (`fixed_budget = 10`) to minimize resource usage.
- **Target List:** Uses a reduced IPv6 target list of **20 prefixes** for lightweight test runs.
- **Agent Configuration:** Uses the `lip6` agent tag instead of `gcp-mlab`, targeting a controlled testing environment.
- **GitHub Actions Integration:**
  - Runs on the `test_scheduler` branch with a dedicated cron schedule.
  - Connects to the **Iris development API** using credentials from GitHub Secrets (`IRIS_DEV_*`).

## Purpose

The test scheduler enables **safe testing of scheduling logic**, validation of measurement flow and debugging in a controlled environment before deploying changes to production.
