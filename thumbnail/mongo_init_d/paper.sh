#!/bin/bash

mongoimport -u root -p example --db paper --collection paper \
  --file /docker-entrypoint-initdb.d/paper_dump.json --jsonArray \
  --drop --authenticationDatabase admin --host 127.0.0.1 --port 27017