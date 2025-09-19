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
const buttonContainer = document.getElementById("button-container");
const denyReasonInput = document.getElementById("deny-reason-input");
const clickMarker = document.getElementById("target-marker");

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
    if (permCheckResult['pending'] == true) {
      nextActionTextDiv.innerHTML = permCheckResult['details'];
      buttonContainer.style.display = 'block';
      nextActionInnerContent.style.display = 'block';
    } else if (permCheckResult['granted'] == true) {
      buttonContainer.style.display = 'none';
      nextActionInnerContent.style.display = 'block';
      nextActionTextDiv.innerHTML = "The last action was APPROVED. Processing...";
    } else if (permCheckResult['granted'] == false) {
      buttonContainer.style.display = 'none';
      nextActionInnerContent.style.display = 'block';
      nextActionTextDiv.innerHTML = "The last action was DENIED. Processing...";
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

  // Only display the marker for the "clickable" object when in PENDING state
  if (permCheckResult['pending'] == true) {
    const click_params = json.click_params;

    if (typeof click_params === 'object' && click_params !== null) {
        const displayed_width = sessionIdEl.clientWidth;
        const displayed_height = sessionIdEl.clientHeight;
        const scale_x = displayed_width / click_params.width;
        const scale_y = displayed_height / click_params.height;
        const new_x = click_params.x * scale_x;
        const new_y = click_params.y * scale_y;

        clickMarker.style.left = `${new_x}px`;
        clickMarker.style.top = `${new_y}px`;
        clickMarker.style.display = 'block';
    } else {
        clickMarker.style.display = 'none';
    }
  } else {
      clickMarker.style.display = 'none';
  }

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

document.getElementById("deny-action").onclick = async function(e) {
  const reason = denyReasonInput.value.trim();

  const response = await fetch(`/sessions/${sessionId}/complete_perm_check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify(
          {
            "granted": false,
            "reason": reason || "denied"
          }
        )
      });
    const json = await response.json();
    console.log(json);
};

updateScreenshot().then(() => console.log("initialized"));