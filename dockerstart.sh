#!/bin/bash

# Simple commands to start the autobidder and webserver. Although both are
# started in separate threads, it should be noted that no failure recovery is
# present.
export SJSITE="/home/webpage/"
python -m sjautobidder &
gunicorn sjautobidder.reporting.webserver -b '0.0.0.0:80'
