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
const screenViewTextEl = document.getElementById("screen-view-text");
const nextActionInnerContent = document.getElementById("next-action-inner-content");
const nextActionTextDiv = document.getElementById("next-action-description");
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('session_id');
const apiKey = urlParams.get('api_key');
console.log(`Starting session viewer for ${sessionId}`);

const updateScreenshot = async () => {

  const permCheck = await fetch(`/sessions/${sessionId}/get_perm_check`, {
      method: 'GET',
    });
  if (permCheck.status == 404) {
    nextActionInnerContent.style.display = 'none'
  }
  else {
    permCheckResult = await permCheck.json();
    if (permCheckResult['pending'] == false) {
      nextActionInnerContent.style.display = 'none'
    } else {
      nextActionInnerContent.style.display = 'block'
      nextActionTextDiv.innerHTML = permCheckResult['details']
    }
  }


  const response = await fetch(`/sessions/${sessionId}/commands`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({name: 'screenshot'}),
    });


  
  if (!response.ok) {
      console.log(`Error processing command: Server error (Status: ${response.status}, message: ${response.text()}})`);
      screenViewTextEl.innerHTML = `Failed to get screenshot! ${response.status}`;
      return;
  }
  const json = await response.json();
  sessionIdEl.src = "data:image/png;base64," + json.screenshot;
  screenViewTextEl.innerHTML = '';
  setTimeout(async () => {
    await updateScreenshot();
  }, 500);
};

document.getElementById("approve-action").onclick = async function(e) {
  const response = await fetch(`/sessions/${sessionId}/complete_perm_check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify(
          {
            "granted": true,
            "reason": "good"
          }
        )
      });
    const json = await response.json();
    console.log(json);
};

updateScreenshot().then(() => console.log("initialized"));