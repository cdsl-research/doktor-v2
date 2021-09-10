#!/bin/bash

DATABASE_NAME=paper
COLLECTION_NAME=paper
MONGO_HOST=mongo

mongoimport -u root -p example --db $DATABASE_NAME --collection $COLLECTION_NAME \
  --file /dump/dump.json --jsonArray \
  --drop --authenticationDatabase admin --host $MONGO_HOST --port 27017