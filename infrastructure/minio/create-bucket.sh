#!/bin/sh
set -eu
mc alias set local "$OBJECT_STORAGE_ENDPOINT" "$OBJECT_STORAGE_ACCESS_KEY" "$OBJECT_STORAGE_SECRET_KEY"
mc mb --ignore-existing "local/$OBJECT_STORAGE_BUCKET"

