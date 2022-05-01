#!/usr/bin/env bash

# shellcheck disable=SC2045
for fname in $(ls openapi_*.json)
do
    SERVICE_NAME=$(basename -s ".json" "$fname")
    ./node_modules/.bin/redoc-cli bundle "$fname" \
        --options.theme.colors.primary.main=orange \
        --output="../docs/${SERVICE_NAME}.html"
    LINK_LIST="$LINK_LIST
    <li><a href='$SERVICE_NAME.html'>$SERVICE_NAME</a></li>"
done

rm ../docs/index.html
cat <<EOF | tee ../docs/index.html
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>ReDoc Index</title>
</head>
<body>
  <h1>ReDoc Index</h1>
  <ul>
    $LINK_LIST
  </ul>
</body>
</html>
EOF