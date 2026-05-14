#!/bin/bash

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_URL="https://mirrors.tencent.com/repository/generic/ai-coding/ai-kit"
REPO_NAME="ai-kit"
ARCHIVE_NAME="${REPO_NAME}.zip"

echo "Starting upload..."

cd "$SCRIPT_DIR"
if [ -f "$ARCHIVE_NAME" ]; then
    rm "$ARCHIVE_NAME"
fi

git archive --format=zip -o "$ARCHIVE_NAME" HEAD

echo "Archive created: $ARCHIVE_NAME"

if [ -z "$MIRROR_AUTH" ]; then
    echo "Error: MIRROR_AUTH not set"
    exit 1
fi

RESPONSE=$(curl -w "\n%{http_code}" -u "$MIRROR_AUTH" \
    --upload-file "$SCRIPT_DIR/$ARCHIVE_NAME" \
    "$REPO_URL/$ARCHIVE_NAME" \
    2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "Upload successful (HTTP $HTTP_CODE)"
    echo "File URL: $REPO_URL/$ARCHIVE_NAME"
else
    echo "Upload failed (HTTP $HTTP_CODE)"
    exit 1
fi
