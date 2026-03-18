#!/bin/sh

CONFIG_PATH=$(mktemp)
DATA_PATH=$(mktemp)

# We set domain explicitly to fix the y axis (rather than let it be computed).
# We must hard-code x1 and x2 at -1 and 3 (len(["ai", "human", "monkey"])).
cat >$CONFIG_PATH <<EOF
{
  "writer": {
    "width": 300,
    "height": 400,
    "output_path": "examples/boxplot.svg",
    "css": ["examples/style.css"]
  },
  "plot": {
    "margins": { "top": 10, "bottom": 10, "left": 50 },
    "y_axis_values": { "max_count": 5 },
    "y_label": "ln(actual / estimate)",
    "domain": { "y1": 0, "y2": 20 }
  },
  "data_path": "$DATA_PATH"
}
EOF

# Provides samples for 3 different distributions.
# Order is irrelevant.
cat >$DATA_PATH <<EOF
ai 12
ai 15
ai 19
ai 10
ai 9
human 12
human 15
human 18
human 12
monkey 5
monkey 3
monkey 12
monkey 9
ai 10
EOF

python3 src/main.py boxplot --config $CONFIG_PATH
