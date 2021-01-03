#! /bin/bash

# Load data from our benchmark
data=$(cat ${COND_DEPS}/results.csv)

# Generate graphs...

# Write the data out
echo "$data" > ${COND_OUT}/graph.csv
