#! /bin/bash

echo "This is a long running task."
echo "Press Ctrl-C or send SIGTERM to Conductor to abort."
sleep 3

./count.sh
