# Computer Use Preview

## Quick Start

This section will guide you through setting up and running the Computer Use Preview model, either the Gemini Developer API or Vertex AI. Follow these steps to get started.

### 1. Installation

**Clone the Repository**

```bash
git clone https://github.com/google/computer-use-preview.git
cd computer-use-preview
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
You can get started using either the Gemini Developer API or Vertex AI.

#### A. If using the Gemini Developer API:

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

#### B. If using the Vertex AI Client:

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
python main.py --query "Go to Google and type 'Hello World' into the search bar"
```

**Available Environments:**

You can specify a particular environment with the ```--env <environment>``` flag.  Available options:

- `playwright`: Runs the browser locally using Playwright.
- `browserbase`: Connects to a Browserbase instance.
- `agentcore`: Connects to Amazon Bedrock AgentCore Browser.

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

**Amazon Bedrock AgentCore**

Runs the agent using Amazon Bedrock AgentCore Browser as the backend. Requires AWS credentials configured and the `bedrock-agentcore` Python package installed.

```bash
python main.py --query="Search for great deals on Alexa devices" --env="agentcore"
```

The AWS region is automatically detected from your AWS configuration (environment variables, ~/.aws/config, or IAM role). You can override it by setting:

```bash
export AWS_REGION="us-east-1"
```

**Session Recording (AgentCore only)**

Enable session recording to S3 for replay and debugging:

```bash
# Auto-create IAM role (recommended)
python main.py --query="Search for great deals on Alexa devices" --env="agentcore" \
  --recording_bucket="my-recordings-bucket" \
  --create_execution_role

# Or provide existing role
python main.py --query="Search for great deals on Alexa devices" --env="agentcore" \
  --recording_bucket="my-recordings-bucket" \
  --recording_prefix="sessions" \
  --execution_role_arn="arn:aws:iam::123456789012:role/AgentCoreRecordingRole"
```

The auto-created role is scoped to the specified S3 bucket/prefix with minimal permissions:
- Trust policy: `bedrock-agentcore.amazonaws.com`
- S3 permissions: `s3:PutObject`, `s3:ListMultipartUploadParts`, `s3:AbortMultipartUpload`

Recordings can be viewed using the AgentCore session replay viewer.

## Agent CLI

The `main.py` script is the command-line interface (CLI) for running the browser agent.

### Command-Line Arguments

| Argument | Description | Required | Default | Supported Environment(s) |
|-|-|-|-|-|
| `--query` | The natural language query for the browser agent to execute. | Yes | N/A | All |
| `--env` | The computer use environment to use. Must be one of the following: `playwright`, `browserbase`, or `agentcore` | No | playwright | All |
| `--initial_url` | The initial URL to load when the browser starts. | No | https://www.google.com | All |
| `--highlight_mouse` | If specified, the agent will attempt to highlight the mouse cursor's position in the screenshots. This is useful for visual debugging. | No | False (not highlighted) | `playwright` |
| `--recording_bucket` | S3 bucket name for session recording (bucket name only, not ARN). Example: `my-recordings-bucket` | No | None | `agentcore` |
| `--recording_prefix` | S3 prefix for session recordings. | No | recordings | `agentcore` |

### Environment Variables

| Variable | Description | Required |
|-|-|-|
| GEMINI_API_KEY | Your API key for the Gemini model. | Yes |
| BROWSERBASE_API_KEY | Your API key for Browserbase. | Yes (when using the browserbase environment) |
| BROWSERBASE_PROJECT_ID | Your Project ID for Browserbase. | Yes (when using the browserbase environment) |
| AWS_REGION | AWS region for AgentCore Browser. | No (auto-detected from AWS config when using agentcore environment) |
