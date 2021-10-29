#!/bin/bash

DATABASE_NAME=author
COLLECTION_NAME=author
MONGO_HOST=author-mongo

mongoimport -u root -p example --db $DATABASE_NAME --collection $COLLECTION_NAME \
  --file /dump/dump.json --jsonArray \
  --drop --authenticationDatabase admin --host $MONGO_HOST --port 27017