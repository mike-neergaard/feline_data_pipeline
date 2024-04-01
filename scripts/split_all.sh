for f in raw/*; do
	name=${f:4:24}
	echo "Processing $name"
	source scripts/split.sh $name
done
