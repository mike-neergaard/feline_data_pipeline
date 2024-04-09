#!/bin/bash

for f in ./"New Recording"*; do 
	echo "Processing $f" 
	new_file=$(exiftool "$f" |
		# Extract the creation date line
		grep "Media Create Date" | 
		# Kill everything up to the actual date
		sed 's/: /###/' | 
		sed 's/.*###//' | 
		# Change YYYY:MM:DD to YYYY-MM-DD
		sed 's/:/-/' | 
		sed 's/:/-/' | 
		# T goes between year and time, Z goes at the end
		sed 's/ /T/' | 
		sed 's/$/Z/' |
		# Add file extension 
		sed 's/$/.wav/' 
	)
	# Sox can't handle m4a, so change format to wav
	ffmpeg -y -i "$f" "raw/$new_file"
	# We're done with the original file
	mv --backup=numbered "$f" processed
	# Split audio file into chunks
	source scripts/split.sh "$new_file" 
done
# Ask the user which sounds are cat sounds
source scripts/select.sh
