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

**hud**

Runs the agent using hud's browser environment. This is the same environment used by `hud_eval.py` but can be run directly with `main.py` for individual tasks. Ensure the `HUD_API_KEY` environment variable is set.

```bash
python main.py --query="Go to Google and type 'Hello World' into the search bar" --env="hud"
```

## Agent CLI

The `main.py` script is the command-line interface (CLI) for running the browser agent.

### Command-Line Arguments

| Argument | Description | Required | Default | Supported Environment(s) |
|-|-|-|-|-|
| `--query` | The natural language query for the browser agent to execute. | Yes | N/A | All |
| `--env` | The computer use environment to use. Must be one of the following: `playwright`, or `browserbase` | No | N/A | All |
| `--initial_url` | The initial URL to load when the browser starts. | No | https://www.google.com | `playwright` |
| `--highlight_mouse` | If specified, the agent will attempt to highlight the mouse cursor's position in the screenshots. This is useful for visual debugging. | No | False (not highlighted) | `playwright` |

### Environment Variables

| Variable | Description | Required |
|-|-|-|
| GEMINI_API_KEY | Your API key for the Gemini model. | Yes |
| BROWSERBASE_API_KEY | Your API key for Browserbase. | Yes (when using the browserbase environment) |
| BROWSERBASE_PROJECT_ID | Your Project ID for Browserbase. | Yes (when using the browserbase environment) |
| HUD_API_KEY | Your API key for hud. Required for running evaluations with hud_eval.py. | Yes (when using the hud enviornment or running hud_eval.py) |

## Evaluations

The `hud_eval.py` script allows you to run automated evaluations against hud tasksets:

```bash
python hud_eval.py --taskset <taskset_id> [--parallel] [--max_concurrent <n>]
```

**Arguments:**
- `--taskset`: The HUD taskset ID to evaluate (e.g., 'OSWorld-Verified')
- `--parallel`: Run tasks in parallel (default: serial execution)
- `--max_concurrent`: Maximum concurrent tasks when running in parallel (default: 3)
- `--model`: Model name (default: 'gemini-2.0-flash-exp')
- `--api_key`: Gemini API key (uses GEMINI_API_KEY env var if not provided)

**Example:**
```bash
# Run a taskset serially
python hud_eval.py --taskset SheetBench-V2

# Run in parallel with 50 concurrent tasks (can support up to 400)
python hud_eval.py --taskset OSWorld-Verified --parallel --max_concurrent 50
```

## Computers

For an in-depth explanation of how the system works, please see the instructions document available here:

https://docs.google.com/document/d/1jTWQPVCIso7mo5SbQCn2DKZXWFlL_g3D2f-JOrZa1do/edit?tab=t.0