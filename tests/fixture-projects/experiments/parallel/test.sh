#! /bin/bash

echo $COND_SLOT > $COND_OUT/slot.txt
echo $1 > $COND_OUT/arg1.txt
echo "stdout $COND_SLOT"
echo "stderr $COND_SLOT" >&2
