#!/bin/bash -x

# FILES=$(curl -s https://ja.tak-cslab.org/tech-report | grep -oP 'https://drive.google.com/[^\s]+sharing' | cut -d/ -f 6)
LINES=$(curl -s https://ja.tak-cslab.org/tech-report | grep -oP '<li><a .*?</a>')
IFS=""

for l in $LINES
do
    echo $l | grep -o '">.*\?</' | cut -c3- | rev | cut -c3- | rev
done
