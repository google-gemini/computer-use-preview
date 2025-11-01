import os

import termcolor
from playwright.sync_api import sync_playwright

from ..playwright.playwright import PlaywrightComputer
from . import utils


class AgentCoreComputer(PlaywrightComputer):
    """Connects to Amazon Bedrock AgentCore Browser via CDP.

    Supports optional session recording to S3 for replay and debugging.
    """

    def __init__(
        self,
        screen_size: tuple[int, int],
        initial_url: str = "https://www.google.com",
        recording_bucket: str | None = None,
        recording_prefix: str = "recordings",
        execution_role_arn: str | None = None,
        create_execution_role: bool = False,
        browser_identifier: str | None = None,
        region: str | None = None,
    ):
        from boto3.session import Session

        super().__init__(screen_size, initial_url)
        self._recording_bucket: str | None = recording_bucket
        self._recording_prefix: str = recording_prefix
        self._execution_role_arn: str | None = execution_role_arn
        self._create_execution_role: bool = create_execution_role
        self._browser_identifier: str = (
            browser_identifier or
            os.getenv("AGENTCORE_BROWSER_IDENTIFIER", "aws.browser.v1")
        )
        # Determine region with fallback chain
        boto_region = Session().region_name
        self._region: str = (
            region
            or os.getenv("AGENTCORE_REGION")
            or os.getenv("AWS_REGION")
            or (boto_region if isinstance(boto_region, str) else None)
            or "us-west-2"
        )
        self._created_browser: bool = False
        self._client = None

    def __enter__(self):
        from bedrock_agentcore.tools.browser_client import BrowserClient

        print("Creating AgentCore browser session...")

        region = self._region

        # Create browser with recording if bucket specified
        browser_identifier_to_use = self._browser_identifier
        if self._recording_bucket:
            # If browser_identifier is already a browser ID (starts with "br-"), use it directly
            if self._browser_identifier.startswith("br-"):
                termcolor.cprint(
                    f"Using provided browser ID: {self._browser_identifier}",
                    color="cyan"
                )
                browser_identifier_to_use = self._browser_identifier
            else:
                # Create a unique browser name based on the bucket and prefix
                # This ensures each recording configuration gets its own browser
                import hashlib
                config_hash = hashlib.sha256(
                    f"{self._recording_bucket}/{self._recording_prefix}".encode()
                ).hexdigest()[:8]
                browser_name = f"recording_{config_hash}"
                
                self._execution_role_arn, browser_id = utils.setup_browser_recording(
                    browser_name,
                    self._browser_identifier,
                    self._recording_bucket,
                    self._recording_prefix,
                    self._execution_role_arn,
                    self._create_execution_role,
                    region
                )
                # Use the custom browser ID instead of the original identifier
                browser_identifier_to_use = browser_id

        self._client = BrowserClient(region)

        session_id = self._client.start(
            identifier=browser_identifier_to_use,
            name="gemini-browser-session"
        )
        print(f"AgentCore browser session started: {session_id}")

        ws_url, headers = self._client.generate_ws_headers()

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(
            ws_url,
            headers=headers
        )
        self._context = self._browser.contexts[0]
        self._page = self._context.pages[0]

        # Set viewport explicitly (CDP connection doesn't inherit from session config)
        self._page.set_viewport_size({
            "width": self._screen_size[0],
            "height": self._screen_size[1]
        })

        self._page.goto(self._initial_url)

        self._context.on("page", self._handle_new_page)

        termcolor.cprint(
            f"AgentCore browser session started in {region}",
            color="green",
            attrs=["bold"],
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up in reverse order, with error handling for each step
        try:
            if self._page:
                self._page.close()

            if self._context:
                self._context.close()

            if self._browser:
                self._browser.close()
        finally:
            try:
                if self._client:
                    _ = self._client.stop()
            finally:
                try:
                    if self._playwright:
                        self._playwright.stop()
                finally:
                    termcolor.cprint(
                        "AgentCore browser session stopped",
                        color="green",
                        attrs=["bold"],
                    )

