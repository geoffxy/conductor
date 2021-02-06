#! /bin/bash

# This script simply prints all of its arguments into a file
> ${COND_OUT}/all_options.txt
for i; do
  echo $i >> ${COND_OUT}/all_options.txt
done
