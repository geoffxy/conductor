#! /bin/bash

# Usage: ./sweep.sh <integer>

if [ "$(($1 % 2))" -eq 0 ]; then
  # This script exits with a non-zero code if the first argument is even.
  exit 1
else
  echo $(date +%s) > $COND_OUT/date.txt
fi
