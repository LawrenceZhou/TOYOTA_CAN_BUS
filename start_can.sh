#!/bin/bash

dt=$(date '+%d-%m-%Y-%H:%M:%S');

# start the python can script and save

python toyotaCan.py -c can0 -i socketcan -f "$dt.txt"
