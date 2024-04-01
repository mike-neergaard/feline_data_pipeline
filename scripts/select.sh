#!/bin/bash
for f in bursts/*; do
    fname=${f:7:27}
    echo "Processing $fname"
    valid="r"
    # It feels good to assign this variable before use
    play_sound="Y"
    while [ $valid == "r" ]; do 
	    if [ $play_sound == "Y" ] ; then 
		    play -q $f 
	    fi
	    play_sound="Y"

	    cat scripts/select_menu_1.0.txt
	    read -p "" valid 
	    # Default is yes
	    if [ -z "$valid" ]; then 
		    valid="y" 
	    fi
	    # Take first letter, lowercase 
	    valid=${valid,}
	    valid=${valid::1} 

	    if [ $valid == "y" ] ; then 
		    mv $f signals 
		    echo "Saved" 
	    elif [ $valid == "n" ]; then 
		    rm $f 
	    elif [ $valid == "t" ]; then 
		    mv $f signals/trim_$fname
		    echo "Saved" 
	    elif [ $valid == "m" ]; then 
		    mv $f signals/multi_$fname
		    echo "Saved" 
	    elif [ $valid != "r" ]; then
		    echo "Please enter a valid response"
		    play_sound="N"
		    valid="r"
	    fi
    done
done
