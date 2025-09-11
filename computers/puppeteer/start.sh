#!/bin/bash

Xvfb :99 -ac -screen 0 1920x1080x24 &

sleep 0.2s

export PORT=8080
export HEADFULCHROME=true
export USE_PUBSUB=true

node dist/index.js
