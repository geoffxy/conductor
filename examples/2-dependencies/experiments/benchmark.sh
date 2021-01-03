#! /bin/bash

value=$(($RANDOM % 10000))

echo "config,run_time_ms" > ${COND_OUT}/results.csv
echo "testing,$value" >> ${COND_OUT}/results.csv
