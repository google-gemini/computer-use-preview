#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if [ "${HEADFULCHROME,,}" = "true" ]; then
  # start the display server if we are running headful chrome
  Xvfb -ac $DISPLAY -screen 0 $SCREEN_RESOLUTION > /dev/null 2>&1 &
fi

if [ "${FULLOS,,}" = "true" ]; then
  # start the display server if we are running full os
  # Xvfb -ac $DISPLAY -screen 0 1000x1000x16 > /dev/null 2>&1 &
  # x11vnc -display :99 -forever -rfbauth /home/myuser/.vncpass -listen 0.0.0.0 -rfbport 5900 >/dev/null 2>&1 & \
  startxfce4 >/dev/null 2>&1 &
  sleep 2 && echo 'Container running!'
fi

# start the Nodejs signalling code
node dist/index.js



