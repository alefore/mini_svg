#!/bin/sh

awk '{print $1, log($2/$3);}' <examples/productivity_boxplot/data.txt | \
python3 src/main.py examples/productivity_boxplot/config.json >examples/productivity_boxplot/output.svg
