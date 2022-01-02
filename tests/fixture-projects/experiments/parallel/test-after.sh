#! /bin/bash

if [ -f "$COND_DEPS/slot.txt" ]; then
  echo $COND_SLOT > $COND_OUT/slot.txt
else
  echo "Dependency slot.txt did not exist!" >&2
  exit 1
fi
