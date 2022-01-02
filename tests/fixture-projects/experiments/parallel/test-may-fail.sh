#! /bin/bash

echo $COND_SLOT > $COND_OUT/slot.txt
echo $1 > $COND_OUT/arg1.txt

if [ "$(($1 % 2))" -eq 0 ]; then
  # This script exits with a non-zero code if the first argument is
  # even.
  exit 1
else
  echo "stdout $COND_SLOT"
  echo "stderr $COND_SLOT" >&2
fi
