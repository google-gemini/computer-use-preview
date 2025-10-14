# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Authentication module for Playwright browser automation.
Handles login flows based on TOML configuration files.
"""

import os
import time
import toml
import termcolor
from typing import Optional, Dict, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class AuthConfig:
    """Configuration for a single authentication site."""
    
    def __init__(self, site_name: str, config: Dict[str, Any]):
        self.site_name = site_name
        self.name = config.get("name", site_name)
        self.login_url = config["login_url"]
        self.success_url = config.get("success_url", "")
        self.username_env = config["username_env"]
        self.password_env = config["password_env"]
        
        # Selectors
        selectors = config.get("selectors", {})
        self.username_field = selectors.get("username_field", "")
        self.password_field = selectors.get("password_field", "")
        self.submit_button = selectors.get("submit_button", "")
        self.success_element = selectors.get("success_element", "")
        self.timeout = selectors.get("timeout", 30)
        
    def get_credentials(self) -> tuple[str, str]:
        """Retrieve credentials from environment variables."""
        username = os.environ.get(self.username_env)
        password = os.environ.get(self.password_env)
        
        if not username or not password:
            raise ValueError(
                f"Missing credentials for {self.name}. "
                f"Please set {self.username_env} and {self.password_env} in .env file"
            )
        
        return username, password


class PlaywrightAuthenticator:
    """Handles authentication for Playwright browser sessions."""
    
    def __init__(self, config_path: str = "playwright-auth.toml"):
        """
        Initialize the authenticator with a TOML configuration file.
        
        Args:
            config_path: Path to the TOML configuration file
        """
        self.config_path = config_path
        self.config_data = self._load_config()
        self.default_site = self.config_data.get("default_site", "")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse the TOML configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Authentication config file not found: {self.config_path}"
            )
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return toml.load(f)
    
    def get_site_config(self, site_name: Optional[str] = None) -> AuthConfig:
        """
        Get configuration for a specific site.
        
        Args:
            site_name: Name of the site. If None, uses default_site.
            
        Returns:
            AuthConfig object for the specified site
        """
        if site_name is None:
            site_name = self.default_site
            
        if not site_name:
            raise ValueError("No site specified and no default_site configured")
        
        sites = self.config_data.get("sites", {})
        if site_name not in sites:
            available = ", ".join(sites.keys())
            raise ValueError(
                f"Site '{site_name}' not found in config. "
                f"Available sites: {available}"
            )
        
        return AuthConfig(site_name, sites[site_name])
    
    def perform_login(
        self, 
        page: Page, 
        site_name: Optional[str] = None,
        verbose: bool = True
    ) -> str:
        """
        Perform login on the specified site.
        
        Args:
            page: Playwright Page object
            site_name: Name of the site to login to. If None, uses default_site.
            verbose: Whether to print progress messages
            
        Returns:
            The success URL after login
        """
        config = self.get_site_config(site_name)
        
        if verbose:
            termcolor.cprint(
                f"Performing authentication for {config.name}...",
                color="cyan",
                attrs=["bold"],
            )
        
        # Get credentials from environment
        username, password = config.get_credentials()
        
        # Navigate to login page
        if verbose:
            print(f"  → Navigating to login page: {config.login_url}")
        page.goto(config.login_url)
        page.wait_for_load_state("networkidle", timeout=config.timeout * 1000)
        
        # Wait a bit for any dynamic content to load
        time.sleep(1)
        
        # Fill username
        if verbose:
            print(f"  → Filling username field")
        try:
            # Try as CSS selector first
            page.fill(config.username_field, username, timeout=5000)
        except PlaywrightTimeoutError:
            # Try as label text
            page.get_by_label(config.username_field).fill(username)
        
        # Fill password
        if verbose:
            print(f"  → Filling password field")
        try:
            # Try as CSS selector first
            page.fill(config.password_field, password, timeout=5000)
        except PlaywrightTimeoutError:
            # Try as label text
            page.get_by_label(config.password_field).fill(password)
        
        # Click submit button
        if verbose:
            print(f"  → Clicking submit button")
        try:
            # Try as CSS selector first
            page.click(config.submit_button, timeout=5000)
        except PlaywrightTimeoutError:
            # Try as button text
            page.get_by_role("button", name=config.submit_button).click()
        
        # Wait for navigation after login
        if verbose:
            print(f"  → Waiting for authentication to complete...")
        
        # Wait for either success URL or success element
        if config.success_url:
            try:
                page.wait_for_url(
                    config.success_url, 
                    timeout=config.timeout * 1000
                )
            except PlaywrightTimeoutError:
                # If exact URL match fails, just wait for load state
                page.wait_for_load_state("networkidle", timeout=config.timeout * 1000)
        else:
            page.wait_for_load_state("networkidle", timeout=config.timeout * 1000)
        
        # Optionally wait for a specific element to verify login
        if config.success_element:
            try:
                page.wait_for_selector(
                    config.success_element, 
                    timeout=config.timeout * 1000
                )
            except PlaywrightTimeoutError:
                termcolor.cprint(
                    f"Warning: Success element '{config.success_element}' not found",
                    color="yellow"
                )
        
        # Additional wait to ensure page is fully loaded
        time.sleep(1)
        
        if verbose:
            termcolor.cprint(
                f"✓ Authentication successful for {config.name}",
                color="green",
                attrs=["bold"],
            )
        
        # Return the URL to navigate to (or current URL if success_url not specified)
        return config.success_url if config.success_url else page.url
    
    def list_available_sites(self) -> list[str]:
        """Return a list of all configured sites."""
        return list(self.config_data.get("sites", {}).keys())
