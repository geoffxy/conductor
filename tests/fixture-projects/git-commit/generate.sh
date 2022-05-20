#! /bin/bash

# Fail this script when the "fail" file exists and the argument to this script
# is 1. We use this to simulate partial task failure.
if [ -f fail ] && [ $1 = "1" ]; then
  exit 1
fi

cp source.txt $COND_OUT/out.txt
echo $1 >> $COND_OUT/out.txt
