#!/usr/bin/bash

ENTRY_POINTS="src/mini_svg.py"

TESTS=""

if [ -z "$ENTRY_POINTS" ]; then
  echo "Must define entry points (in agent/validate.sh)."
  exit 1
fi

exit_status=0

function run_command {
  local command="$1"
  local tmp_output
  tmp_output=$(mktemp)

  echo "Running: $command"
  if ! eval "$command" >"$tmp_output" 2>&1; then
    echo "Command failed: $command" >&2
    cat "$tmp_output" >&2
    exit_status=1
  fi

  rm -f "$tmp_output"
}

# Determine VALIDATE_PYTHON if not already set or empty
if [ -z "${VALIDATE_PYTHON}" ]; then
  if [ -f ~/local/bin/python3 ]; then
    VALIDATE_PYTHON=~/local/bin/python3
  elif [ -f ~/bin/python3 ]; then
    VALIDATE_PYTHON=~/bin/python3
  else
    VALIDATE_PYTHON=python3
  fi
fi

for file in $ENTRY_POINTS; do
  run_command "~/bin/mypy --strict $file"
done

for file in $TESTS; do
  run_command "${VALIDATE_PYTHON} -m pytest $file"
done

exit $exit_status
