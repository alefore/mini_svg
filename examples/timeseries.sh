#!/usr/bin/sh

# See https://github.com/alefore/weblog/blob/master/smoothing.md
# for exponential-smooth.

set -e

if [ "$#" -ne 1 ]; then
    echo "Error: Exactly 1 argument required."
    echo "Usage: $0 [git_repos_dir]"
    exit 1
fi

DATA=$(mktemp -d)

( cd $1 && git log --format="%ct" ) | sort -n >$DATA/commits.txt

for life in 30d 90d 365d
do
  exponential-smooth --half_life=$life --output_rate=1d --output_resolution=2d \
    <$DATA/commits.txt | \
  awk '{print "'$life'", $1, $2;}' >>$DATA/timeseries.txt
done

python3 ~/mini_svg/src/main.py examples/timeseries.json >examples/timeseries.svg <$DATA/timeseries.txt
