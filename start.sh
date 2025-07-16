#!/bin/bash

set -euxo pipefail

#
# $GITHUB_PAT and $REPO_URL are initialized as environment variables
# by docker-compose.
#
if [ -z "${GITHUB_PAT:-}" ] || [ -z "${REPO_URL:-}" ]; then
	echo "GITHUB_PAT and/or REPO_URL not set"
	exit 1
fi

# Define potential stale runner state files
RUNNER_STATE_FILES=(".runner" ".runner_migrated")

# Remove stale runner state files
for file in "${RUNNER_STATE_FILES[@]}"; do
	rm -f "${file}"
done

REPO_PATH="${REPO_URL/https:\/\/github.com\//}"
TOKEN_URL="https://api.github.com/repos/${REPO_PATH}/actions/runners/registration-token"
RUNNER_TOKEN=$(curl -s -X POST "${TOKEN_URL}" \
		-H "Authorization: token ${GITHUB_PAT}" \
		-H "Accept: application/vnd.github.v3+json" | jq -r .token)
if [ -z "${RUNNER_TOKEN}" ] || [ "${RUNNER_TOKEN}" == "null" ]; then
	echo "failed to fetch runner token from GitHub API"
	exit 1
fi

RUNNER_NAME="${RUNNER_NAME:-github-runner-iris-production}"
LABELS="${LABELS:-iris,production}"
WORK_DIR="${WORK_DIR:-/runner}"
./config.sh \
	--url "${REPO_URL}" \
	--token "${RUNNER_TOKEN}" \
	--name "${RUNNER_NAME}" \
	--labels "${LABELS}" \
	--work "${WORK_DIR}" \
	--unattended \
	--replace

exec ./run.sh
