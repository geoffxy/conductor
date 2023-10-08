#! /bin/bash

prefix=$1
num=$2

if [ $num -gt 1 ] && [ -z "$COND_DEPS" ]; then
  exit 1
fi

if [ $num = 1 || -f "$COND_DEPS/$prefix_$num" ]; then
  next_num=(($num + 1))
  touch $COND_OUT/$prefix_$next_num
  exit 0
else
  exit 1
fi
