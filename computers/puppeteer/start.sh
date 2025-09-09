#!/bin/bash

Xvfb :99 -ac -screen 0 1920x1080x24 &

sleep 3s

node dist/index.js
