#!/bin/bash -x

FILES=$(curl -s https://ja.tak-cslab.org/tech-report | grep -oP 'https://drive.google.com/[^\s]+sharing' | cut -d/ -f 6)

for f in $FILES
do
    if [ -e pdf_files/$f.pdf ]
    then
	echo "exists $f"
    else
        # pip install gdown
        gdown -O pdf_files/$f.pdf "https://drive.google.com/uc?id=$f"
        sleep 300
    fi
done
