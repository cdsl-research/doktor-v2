#!/bin/bash -xe

mongoimport -u root -p example --db author --collection author \
  --file /dump/dump.json --jsonArray \
  --drop --authenticationDatabase admin --host mongo --port 27017