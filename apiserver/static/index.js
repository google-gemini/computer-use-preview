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
const imgEl = document.getElementById("screenshot");

const getAPIKey = () => document.getElementById('api-key').value

const sendCommand = async (sessionId, command) => {
    const response = await fetch(`/sessions/${sessionId}/commands`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': getAPIKey(),
        },
        body: JSON.stringify(command),
      });

    const json = await response.json();
    console.log(json);
    if (!response.ok) {
        alert(`Error processing command: Server error (Status: ${response.status}, message: ${JSON.stringify(json)}})`);
        return;
    }

    imgEl.hidden = false;
    document.getElementById("screenshot").src = "data:image/png;base64," + json.screenshot;
};

const deleteSession = async(sessionId) => {
    const response = await fetch(`/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'X-API-Key': getAPIKey(),
        }
      });
    const json = await response.json();
    console.log(json);
}

const createSession = async function(type) {
    const creatingEl = document.getElementById("creating");
    creatingEl.hidden = false;
    const createWrapperEl = document.getElementById("create-wrapper");
    createWrapperEl.style.display = "none";
    const response = await fetch(`/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': getAPIKey(),
        },
        body: JSON.stringify({type}),
      });
    const json = await response.json();
    if(!response.ok) {
      alert(`Failed to create a session: ${JSON.stringify(json)}`);
      return;
    }
    const sessionId = json.id;
    console.log(json);
    creatingEl.hidden = true;
    const wrapperEl = document.getElementById("watch-wrapper");
    wrapperEl.style.display = "block";
    const sessionIdEl = document.getElementById("session-id");
    sessionIdEl.innerHTML = sessionId;
    const sessionViewerEl = document.getElementById("session-viewer");
    sessionViewerEl.href = `session.html?session_id=${sessionId}&api_key=${getAPIKey()}`;
    // const es = new EventSource(`/sessions/${sessionId}/messages`);
    // es.addEventListener('screenshot', async (event) => {
    //     document.getElementById("screenshot").src = "data:image/png;base64," + event.data;
    //     console.log(event.data);
    // });
    // es.addEventListener('command', async (event) => {
    //     console.log(event.data);
    // });
    document.getElementById("end-session").onclick =  async function(e) {
      deleteSession(sessionId);
      imgEl.removeAttribute("src");
      imgEl.hidden = true;
      wrapperEl.style.display = "none";
      createWrapperEl.style.display = "block";
      sessionIdEl.innerHTML = "";
    }

    document.getElementById("submit-command").onclick =  async function(e) {
        const data = document.getElementById("command").value;
        document.getElementById("command").value = "";
        sendCommand(sessionId, JSON.parse(data));
    }
    document.getElementById("submit-url").onclick =  async function(e) {
      const data = document.getElementById("url").value;
      document.getElementById("url").value = "";
      sendCommand(sessionId, {name: 'navigate', args: {'url': data}});
    }
    document.getElementById("submit-back").onclick =  async function(e) {
      sendCommand(sessionId, {name: 'go_back'});
    }
    document.getElementById("submit-forward").onclick =  async function(e) {
      sendCommand(sessionId, {name: 'go_forward'});
    }
    document.getElementById("submit-screenshot").onclick =  async function(e) {
      sendCommand(sessionId, {name: 'screenshot'});
    }
    document.getElementById('submit-up').onclick = async function(e) {
      sendCommand(sessionId, {name: 'scroll_document', args: {'direction': 'up'}});
    }
    document.getElementById('submit-left').onclick = async function(e) {
      sendCommand(sessionId, {name: 'scroll_document', args: {'direction': 'left'}});
    }
    document.getElementById('submit-right').onclick = async function(e) {
      sendCommand(sessionId, {name: 'scroll_document', args: {'direction': 'right'}});
    }
    document.getElementById('submit-down').onclick = async function(e) {
      sendCommand(sessionId, {name: 'scroll_document', args: {'direction': 'down'}});
    }
    document.getElementById("screenshot").onclick = async (e) => {
        console.log(e.offsetX);
        console.log(e.offsetY);
        await sendCommand(sessionId, {name: 'click_at', args: {'x': e.offsetX, 'y': e.offsetY}});
    }
    let isSelected = false;
    document.onclick = (e) => {
      isSelected = e.target === imgEl;
    }
    window.onkeyup = async (e) => {
      if (isSelected) {
        const key = e.key === ' ' ? 'Space' : e.key;
        await sendCommand(sessionId, {name: 'key_combination', args: {'keys': [key]}});
      }
    }
};

document.getElementById("create-os-session").onclick = async function(e) {
  console.log("creating OS session");
  await createSession("os");
};

document.getElementById("create-browser-session").onclick = async function(e) {
  console.log("creating browser session");
  await createSession("browser");
};

document.getElementById("create-headful-session").onclick = async function(e) {
  console.log("creating headful browser session");
  await createSession("headful");
};