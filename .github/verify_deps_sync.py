# Copyright (C) 2025, François-Guillaume Fernandez.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///

import logging
import sys
import tomllib
from pathlib import Path

import yaml

PRECOMMIT_CONFIG = ".pre-commit-config.yaml"
PYPROJECT_PATH = "./pyproject.toml"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(levelname)s:     %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)


def main():
    # Retrieve & parse all deps files
    deps_dict = {"uv": [], "ruff": [], "ty": [], "mypy": []}
    # Parse precommit
    with Path(PRECOMMIT_CONFIG).open("r") as f:
        precommit = yaml.safe_load(f)
    for repo in precommit["repos"]:
        if repo["repo"] == "https://github.com/astral-sh/uv-pre-commit":
            deps_dict["uv"].append({"file": PRECOMMIT_CONFIG, "version": repo["rev"].lstrip("v")})
        elif repo["repo"] == "https://github.com/charliermarsh/ruff-pre-commit":
            deps_dict["ruff"].append({"file": PRECOMMIT_CONFIG, "version": repo["rev"].lstrip("v")})
    # Parse pyproject.toml
    with Path(PYPROJECT_PATH).open("rb") as f:
        pyproject = tomllib.load(f)

    for dep in pyproject["project"]["optional-dependencies"]["quality"]:
        if dep.startswith("ruff"):
            deps_dict["ruff"].append({"file": PYPROJECT_PATH, "version": dep.split("==")[1]})
        elif dep.startswith("mypy"):
            deps_dict["mypy"] = [{"file": PYPROJECT_PATH, "version": dep.split("==")[1]}]
        elif dep.startswith("ty"):
            deps_dict["ty"] = [{"file": PYPROJECT_PATH, "version": dep.split("==")[1]}]

    # Parse github/workflows/...
    for workflow_file in Path(".github/workflows").glob("*.yml"):
        with workflow_file.open("r") as f:
            workflow = yaml.safe_load(f)
            if "env" in workflow and "UV_VERSION" in workflow["env"]:
                deps_dict["uv"].append(
                    {
                        "file": str(workflow_file),
                        "version": workflow["env"]["UV_VERSION"].lstrip("v"),
                    }
                )

    # Assert all deps are in sync
    troubles = []
    for dep, versions in deps_dict.items():
        versions_ = {v["version"] for v in versions}
        if len(versions_) != 1:
            inv_dict = {v: set() for v in versions_}
            for version in versions:
                inv_dict[version["version"]].add(version["file"])
            troubles.extend(
                [
                    f"{dep}:",
                    "\n".join(f"- '{v}': {', '.join(files)}" for v, files in inv_dict.items()),
                ]
            )

    if len(troubles) > 0:
        raise AssertionError("Some dependencies are out of sync:\n\n" + "\n".join(troubles))
    logger.info("All dependencies are in sync!")


if __name__ == "__main__":
    main()
