import importlib
import inspect
import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import termcolor
from google.genai import types


@dataclass
class FunctionSpec:
    """Configuration for a single custom function."""

    name: str
    module: str
    attribute: str
    description: Optional[str]
    whitelist: bool
    risk_note: Optional[str]


class FunctionRegistry:
    """Loads custom functions from configuration and exposes declarations/execution."""

    def __init__(self, config_path: str, client: Any):
        self._config_path = config_path
        self._client = client
        self._specs: Dict[str, FunctionSpec] = {}
        self._callables: Dict[str, Callable] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load function specs and resolve callables."""
        if not os.path.exists(self._config_path):
            termcolor.cprint(
                f"Function config not found at {self._config_path}; no custom functions loaded.",
                color="yellow",
            )
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as config_file:
                config = json.load(config_file) or {}
        except Exception as exc:
            termcolor.cprint(
                f"Failed to read function config {self._config_path}: {exc}",
                color="red",
            )
            return

        for entry in config.get("functions", []):
            try:
                spec = FunctionSpec(
                    name=entry["name"],
                    module=entry["module"],
                    attribute=entry.get("attribute", entry["name"]),
                    description=entry.get("description"),
                    whitelist=bool(entry.get("whitelist", False)),
                    risk_note=entry.get("risk_note"),
                )
            except KeyError as exc:
                termcolor.cprint(
                    f"Invalid function config entry missing required key {exc}: {entry}",
                    color="red",
                )
                continue

            resolved = self._import_callable(spec)
            if resolved:
                self._specs[spec.name] = spec
                self._callables[spec.name] = resolved

    def _import_callable(self, spec: FunctionSpec) -> Optional[Callable]:
        """Import callable from module according to spec."""
        try:
            module = importlib.import_module(spec.module)
        except Exception as exc:
            termcolor.cprint(
                f"Failed to import module {spec.module} for {spec.name}: {exc}",
                color="red",
            )
            return None

        try:
            func = getattr(module, spec.attribute)
        except AttributeError:
            termcolor.cprint(
                f"Attribute {spec.attribute} not found in module {spec.module}",
                color="red",
            )
            return None

        if not callable(func):
            termcolor.cprint(
                f"{spec.attribute} in module {spec.module} is not callable",
                color="red",
            )
            return None

        if spec.description and not (func.__doc__ and func.__doc__.strip()):
            func.__doc__ = spec.description
        return func

    def function_declarations(self) -> List[types.FunctionDeclaration]:
        """Create function declarations for all loaded functions."""
        declarations: List[types.FunctionDeclaration] = []
        for name, func in self._callables.items():
            try:
                declarations.append(
                    types.FunctionDeclaration.from_callable(
                        client=self._client,
                        callable=func,
                    )
                )
            except Exception as exc:
                termcolor.cprint(
                    f"Failed to build declaration for {name}: {exc}",
                    color="red",
                )
        return declarations

    def has_function(self, name: str) -> bool:
        return name in self._callables

    def is_whitelisted(self, name: str) -> bool:
        return bool(self._specs.get(name) and self._specs[name].whitelist)

    def risk_note(self, name: str) -> Optional[str]:
        spec = self._specs.get(name)
        if not spec:
            return None
        return spec.risk_note

    def execute(self, name: str, args: dict) -> dict:
        if name not in self._callables:
            raise ValueError(f"Function {name} is not registered.")

        func = self._callables[name]
        signature = inspect.signature(func)
        try:
            bound_args = signature.bind(**args)
            bound_args.apply_defaults()
        except TypeError as exc:
            termcolor.cprint(
                f"Invalid arguments for {name}: {exc}",
                color="red",
            )
            raise
        return func(*bound_args.args, **bound_args.kwargs)

