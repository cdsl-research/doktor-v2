#!/bin/bash -x

FILES=$(curl -s https://ja.tak-cslab.org/tech-report | grep -oP 'https://drive.google.com/[^\s]+sharing' | cut -d/ -f 6)

for f in $FILES
do
    # pip install gdown
    gdown -O pdf_files/$f.pdf "https://drive.google.com/uc?id=$f"
    sleep 3
done
