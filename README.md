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

### 2. Configuration

#### Set Gemini API Key (for Gemini Developer API only)

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

#### Setup Vertex AI Client (for Vertex AI API only)

You need to explicitly use Vertex AI, then provide project and location to use the agent:

```bash
export USE_VERTEXAI=true
export VERTEXAI_PROJECT="YOUR_PROJECT_ID"
export VERTEXAI_LOCATION="YOUR_LOCATION"
```

Or to add this to your virtual environment:

```bash
echo 'export USE_VERTEXAI=true' >> .venv/bin/activate
echo 'export VERTEXAI_PROJECT="your-project-id"' >> .venv/bin/activate
echo 'export VERTEXAI_LOCATION="your-location"' >> .venv/bin/activate
# After editing, you'll need to deactivate and reactivate your virtual
# environment if it's already active:
deactivate
source .venv/bin/activate
```

Replace `YOUR_PROJECT_ID` and `YOUR_LOCATION` with your actual project and location.

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
- `hud`: Integrates with hud's browser environment.

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

Runs the agent using Browserbase as the browser backend. Ensure the proper Browserbase environment variables are set:`BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`.

```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --env="browserbase"
```

**HUD**

Runs the agent using HUD's browser environment via the Model Context Protocol (MCP). Ensure the `HUD_API_KEY` environment variable is set.

```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --env="hud"
```

This is the same environment used by `hud_eval.py` but can be run directly with `main.py` for individual tasks.

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
| `--env` | The computer use environment to use. Must be one of the following: `cloud-run`, `playwright`, `browserbase`, or `hud` | No | `cloud-run` | All |
| `--api_server` | The URL of the API Server. | Yes if --env is `cloud-run` | N/A | `cloud-run` |
| `--api_server_key` | The API key for the API Server. If not provided, the script will try to use the `API_SERVER_KEY` environment variable. | No | None (tries `API_SERVER_KEY` env var) | `cloud-run` |
| `--initial_url` | The initial URL to load when the browser starts. | No | https://www.google.com | `playwright`, `hud` |
| `--highlight_mouse` | If specified, the agent will attempt to highlight the mouse cursor's position in the screenshots. This is useful for visual debugging. | No | False (not highlighted) | `playwright` |
| `--model` | The model to use for the agent. | No | computer-use-exp-07-16 | All |

### Environment Variables

| Variable | Description | Required |
|-|-|-|
| GEMINI_API_KEY | Your API key for the Gemini model. | Yes |
| API_SERVER_KEY | The API key for your deployed Cloud Run API server, if it's configured to require one. Can also be provided via the `--api_server_key` argument. | Conditionally (if API server requires it and not passed via CLI) |
| BROWSERBASE_API_KEY | Your API key for Browserbase. | Yes (when using the browserbase environment) |
| BROWSERBASE_PROJECT_ID | Your Project ID for Browserbase. | Yes (when using the browserbase environment) |
| HUD_API_KEY | Your API key for hud. Required for running evaluations with hud_eval.py. | Yes (when using the hud enviornment or running hud_eval.py) |



## Evaluations

The `hud_eval.py` script allows you to run automated evaluations against HUD datasets using the MCP protocol:

```bash
# Run a HuggingFace dataset
python hud_eval.py --dataset hud-evals/sheetbench-50

# Run with custom settings
python hud_eval.py --dataset hud-evals/OSWorld-Verified --model computer-use-exp-07-16 --max-concurrent 10
```

**Arguments:**
- `--dataset`: HuggingFace dataset ID (e.g., 'hud-evals/sheetbench-50') (required)
- `--model`: Model name to use (default: computer-use-exp-07-16)
- `--max-concurrent`: Maximum concurrent tasks (default: 5)
- `--verbose`: Enable verbose output (Note: disables parallel execution when > 1 task)
- `--limit`: Limit number of tasks to run (useful for testing)
- `--name`: Custom name for the evaluation job

The evaluation runner uses the `HudComputer` to connect to HUD's MCP servers, allowing your existing `BrowserAgent` to work seamlessly with HUD's evaluation infrastructure.

## Computers

The system supports multiple computer implementations through the `Computer` interface:

### Available Implementations

1. **CloudRunComputer** - Google Cloud Run-based browser environment
2. **PlaywrightComputer** - Local Playwright-based browser
3. **BrowserbaseComputer** - Browserbase cloud browser service
4. **HudComputer** - HUD environment using Model Context Protocol (MCP)

For an in-depth explanation of how the system works, please see the instructions document available here:

https://docs.google.com/document/d/1jTWQPVCIso7mo5SbQCn2DKZXWFlL_g3D2f-JOrZa1do/edit?tab=t.0

## Advanced Topics

### Cloud Run

Besides the AIS Cloud Run integration, you can also manually deploy the Cloud Run API server yourself:

```bash
gcloud run deploy computer-use-api --image=us-docker.pkg.dev/cloudrun/solutions/computer-use/apiserver:latest --no-invoker-iam-check
```

Warning: the command above deploys a service that allows unauthenticated invocations.
