# Cloud Run Computer Use Tool

## Quick Start

This section will guide you through setting up and running the Cloud Run Computer Use Tool. Follow these steps to get started.

### 1. Installation

**Clone the Repository**
```bash
git clone https://github.com/google/cloud-run-computer-solution.git
cd cloud-run-computer-solution
```

**Set up Python Virtual Environment and Install Dependencies**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Install Playwright and Browser Dependencies**
```bash
# Install system dependencies required by Playwright for Chrome
playwright install-deps chrome

# Install the Chrome browser for Playwright
playwright install chrome
```

### 2. Configuration: Set Gemini API Key

You need a Gemini API key to use the agent:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Or to add this to your virtual environment:

```bash
echo 'export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"' >> .venv/bin/activate
# After editing, you'll need to deactivate and reactivate your virtual
# environment if it's already active:
deactivate
source .venv/bin/activate
```

Replace `YOUR_GEMINI_API_KEY` with your actual key.

### 3. Running the Tool

The primary way to use the tool is via the `main.py` script.

**General Command Structure:**
```bash
python main.py --query "Go to Google and type 'Hello World' into the search bar" --env <environment> [options]
```

**Available Environments:**
* `cloud-run`: Connects to a deployed Cloud Run service (default).
* `playwright`: Runs the browser locally using Playwright.
* `browserbase`: Connects to a Browserbase instance.

**Local Playwright**

Runs the agent using a Chrome browser instance controlled locally by Playwright.

```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --env="playwright"
```
You can also specify an initial URL for the Playwright environment:
```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --env="playwright" --initial_url="https://www.google.com/search?q=latest+AI+news"
```

**Browserbase**

Runs the agent using Browserbase as the browser backend. Ensure your Browserbase environment and any necessary authentications (e.g., API keys via environment variables expected by `BrowserbaseComputer`) are set up.

```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --env="browserbase"
```

**Cloud Run**

Connects to your Cloud Run API Server for computer use. You must provide the URL of your API server.

```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --api_server="https://your-cloud-run-service-url.run.app/"
```
*   Replace `https://your-cloud-run-service-url.run.app/` with the actual URL of your deployed Cloud Run service.
*   If `--env` is not specified, it defaults to `cloud-run`, so providing `--api_server` is sufficient to use this mode.
*   **Note:** When using the Cloud Run environment, the script will print a link to a live stream of screenshots, allowing you to follow the agent's actions in real-time.