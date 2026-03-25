#!/usr/bin/bash
awk -W random=4 'BEGIN { for (i=1; i<=1000; i++) print "distance", sqrt(rand()^2 + rand()^2) }' | \
python3 src/main.py examples/random_distance.json >examples/random_distance.svg
