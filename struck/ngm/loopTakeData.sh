#!/bin/bash
while true
do
  #./loopTakeData.py
  python takeData.py
  sleep 1
  echo "new run, sleep for 1 s"
done

