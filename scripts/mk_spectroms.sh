#!/bin/bash

for f in signals/*; do
	outname=`echo $f|sed 's/wav/png/'`
	sox $f -n spectrogram -o "$outname"
done
