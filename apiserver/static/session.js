// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
const sessionIdEl = document.getElementById("screenshot");
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('session_id');
const apiKey = urlParams.get('api_key');
console.log(`Starting session viewer for ${sessionId}`);

const updateScreenshot = async () => {
  const response = await fetch(`/sessions/${sessionId}/commands`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({name: 'screenshot'}),
    });

  const json = await response.json();
  if (!response.ok) {
      console.log(`Error processing command: Server error (Status: ${response.status}, message: ${JSON.stringify(json)}})`);
  }
  sessionIdEl.src = "data:image/png;base64," + json.screenshot;
  setTimeout(async () => {
    await updateScreenshot();
  }, 1000);
};


updateScreenshot().then(() => console.log("initialized"));