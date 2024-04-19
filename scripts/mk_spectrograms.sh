#!/bin/bash

for f in signals/*.wav; do
	outname=`echo $f|sed 's/wav/png/'`
	sox $f -n spectrogram -o "$outname"
done
