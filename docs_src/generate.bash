#!/usr/bin/env bash

# shellcheck disable=SC2045
for fname in $(ls openapi_*.json)
do
    SERVICE_NAME=$(basename -s ".json" "$fname")
    ./node_modules/.bin/redoc-cli bundle "$fname" \
        --options.theme.colors.primary.main=orange \
        --output="../docs/${SERVICE_NAME}.html"
done