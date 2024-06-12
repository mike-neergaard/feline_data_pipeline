#!/bin/bash
for f in signals/*.wav; do
    fname=${f:8:32}
    echo "Processing $fname"
    clean="r"
    # It feels good to assign this variable before use
    play_sound="Y"
    if test -f "signals/clean/$fname" || test -f "signals/hum/$fname" || test -f "signals/dirty/$fname" ; then 
	    echo "$fname has already been processed"
	    continue
    fi

    while [ $clean == "r" ]; do 
	    if [ $play_sound == "Y" ] ; then 
		    play -q $f 
	    fi
	    play_sound="Y"

	    cat scripts/clean_menu_1.0.txt
	    read -p "" clean 
	    # Default is clean
	    if [ -z "$clean" ]; then 
		    clean="c" 
	    fi
	    # Take first letter, lowercase 
	    clean=${clean,}
	    clean=${clean::1} 

	    if [ $clean == "c" ] ; then 
		    cp $f signals/clean 
		    echo "Saved to clean" 
	    elif [ $clean == "h" ]; then 
		    cp $f signals/hum
		    echo "Saved to hum"
	    elif [ $clean == "d" ]; then 
		    cp $f signals/dirty
		    echo "Saved to dirty" 
	    elif [ $clean != "r" ]; then
		    echo "Please enter a valid response"
		    play_sound="N"
		    clean="r"
	    fi
    done
done
