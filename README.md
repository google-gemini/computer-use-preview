# Computer Use Experimental Solution

## Quick Start

This section will guide you through setting up and running the Computer Use Experimental Solution. Follow these steps to get started.

### 1. Installation

**Clone the Repository**

```bash
git clone https://github.com/google/computer-use-solution-exp.git
cd computer-use-solution-exp
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

- `cloud-run`: Connects to a deployed Cloud Run service (default).
- `playwright`: Runs the browser locally using Playwright.
- `browserbase`: Connects to a Browserbase instance.

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

Runs the agent using Browserbase as the browser backend. Ensure your the proper Browserbase environment variables are set:`BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`.

```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --env="browserbase"
```

**Cloud Run**

Connects to an [API Server](./apiserver/) deployed on Cloud Run for computer use.
You should use the simple one-click deploy setup from AI Studio to obtain the API server address, as well as the API server key.


1. Run the sample code against your Cloud Run API server:

```bash
python main.py \
  --query="Go to Google and type 'Hello World' into the search bar" \
  --api_server="https://your-cloud-run-service-url.run.app/" \
  --api_server_key="your_api_server_key"
```

- Replace `https://your-cloud-run-service-url.run.app/` with the actual URL of your deployed Cloud Run service.
- Replace `your_api_server_key` with the actual API server key.
- If `--env` is not specified, it defaults to `cloud-run`, so providing `--api_server` is sufficient to use this mode.
- **Note:** When using the Cloud Run environment, the script will print a link to a live stream of screenshots, allowing you to follow the agent's actions in real-time.

## Agent CLI

The `main.py` script is the command-line interface (CLI) for running the browser agent.

### Command-Line Arguments

| Argument | Description | Required | Default | Supported Environment(s) |
|-|-|-|-|-|
| `--query` | The natural language query for the browser agent to execute. | Yes | N/A | All |
| `--env` | The computer use environment to use. Must be one of the following: `cloud-run`, `playwright`, or `browserbase` | No | `cloud-run` | All |
| `--api_server` | The URL of the API Server. | Yes if --env is `cloud-run` | N/A | `cloud-run` |
| `--api_server_key` | The API key for the API Server. If not provided, the script will try to use the `API_SERVER_KEY` environment variable. | No | None (tries `API_SERVER_KEY` env var) | `cloud-run` |
| `--initial_url` | The initial URL to load when the browser starts. | No | https://www.google.com | `playwright` |
| `--highlight_mouse` | If specified, the agent will attempt to highlight the mouse cursor's position in the screenshots. This is useful for visual debugging. | No | False (not highlighted) | `playwright` |

### Environment Variables

| Variable | Description | Required |
|-|-|-|
| GEMINI_API_KEY | Your API key for the Gemini model. | Yes |
| API_SERVER_KEY | The API key for your deployed Cloud Run API server, if it's configured to require one. Can also be provided via the `--api_server_key` argument. | Conditionally (if API server requires it and not passed via CLI) |
| BROWSERBASE_API_KEY | Your API key for Browserbase. | Yes (when using the browserbase environment) |
| BROWSERBASE_PROJECT_ID | Your Project ID for Browserbase. | Yes (when using the browserbase environment) |

## Computers

### Interface

The following table outlines the browser interaction commands supported by the system. These commands are invoked by the Gemini model through function calls. All listed commands are supported by `CloudRunComputer`, `PlaywrightComputer`, and `BrowserbaseComputer` implementations.

| Command Name | Description | Arguments (in Gemini Function Call) | Example Gemini Function Call |
|-|-|-|-|
| open_web_browser | Opens the web browser. | None | `{"name": "open_web_browser", "args": {}}` |
| wait_5_seconds | Pauses execution for 5 seconds to allow dynamic content to load or animations to complete. | None | `{"name": "wait_5_seconds", "args": {}}` |
| go_back | Navigates to the previous page in the browser's history. | None | `{"name": "go_back", "args": {}}` |
| go_forward | Navigates to the next page in the browser's history. | None | `{"name": "go_forward", "args": {}}` |
| search | Navigates to the default search engine's homepage (e.g., Google). Useful for starting a new search task. | None | `{"name": "search", "args": {}}` |
| click_at | Clicks at a specific coordinate on the webpage. The x and y values are based on a 1000x1000 grid. | x: int (0-999)<br>y: int (0-999) | `{"name": "click_at", "args": {"x": 500, "y": 300}}` |
| hover_at | Hovers the mouse at a specific coordinate on the webpage. Useful for revealing sub-menus. x and y are based on a 1000x1000 grid. | x: int (0-999)<br>y: int (0-999) | `{"name": "hover_at", "args": {"x": 250, "y": 150}}` |
| type_text_at | Clicks at a specific coordinate and then types the given text. The system automatically presses ENTER after typing. x and y are based on a 1000x1000 grid. | x: int (0-999)<br>y: int (0-999) text: str | `{"name": "type_text_at", "args": {"x": 400, "y": 250, "text": "search query"}}` |
| key_combination | Presses keyboard keys or key combinations. For combinations, keys are specified with "+" (e.g., "Control+C"). Single keys are like "Enter". | keys: str | `{"name": "key_combination", "args": {"keys": "Control+A"}}` |
| navigate | Navigates the browser directly to the specified URL. | url: str | `{"name": "navigate", "args": {"url": "https://www.wikipedia.org"}}` |
| scroll_document | Scrolls the entire webpage "up" or "down". | direction: str ("up" or "down") | `{"name": "scroll_document", "args": {"direction": "down"}}` |



## Advanced Topics


### Cloud Run

Besides the AIS Cloud Run integration, you can also manually deploy the Cloud Run API server yourself:


```bash
gcloud run deploy computer-use-api --image=us-docker.pkg.dev/cloud-run/solutions/computer-use/api-server:latest
```