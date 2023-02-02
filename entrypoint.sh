#!/bin/sh

while [[ 1 -eq 1 ]] ; do
	DATE=$(date)
	python3 -u GuideScraper.py
	echo "Last run time: $DATE"
	echo "Will run in $SLEEPTIME seconds"
	sleep "$SLEEPTIME"
done