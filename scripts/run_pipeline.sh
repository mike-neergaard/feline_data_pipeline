#!/bin/bash

# If for some reason we get caught with unprocessed audio files,
# we need a script to process them, so we separate that into the
# process script
python3 retrieve_cloud_data.py
source scripts/process.sh
