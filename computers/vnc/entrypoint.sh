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


# Start the VNC and X11 servers
Xtigervnc -desktop tigervnc -geometry $SCREEN_RESOLUTION -listen tcp -rfbport 5900 -ac -SecurityTypes None -AlwaysShared -AcceptKeyEvents -AcceptPointerEvents -SendCutText -AcceptCutText $DISPLAY 2>&1 &
# Start novnc proxy
/usr/local/noVNC/utils/novnc_proxy --listen 6080 --vnc localhost:5900 --web /usr/local/noVNC --file-only 2>&1 &
# start nginx reverse proxy to expose everything on a single port
nginx 2>&1 &
# start the Nodejs signalling code
node dist/index.js