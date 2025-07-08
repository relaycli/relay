ENGINE_DIR = .
CLI_DIR = ./cli
DOCS_DIR = ./docs
PYPROJECT_CONFIG_FILE = ${ENGINE_DIR}/pyproject.toml
PYTHON_REQ_FILE = /tmp/requirements.txt
REPO_OWNER ?= relaycli
REPO_NAME ?= relay

.PHONY: help install install-quality lint-check lint-format precommit typing-check deps-check quality style init-gh-labels init-gh-settings install-mintlify start-mintlify

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

########################################################
# Code checks
########################################################

install: ${ENGINE_DIR} ${PYPROJECT_CONFIG_FILE} ## Install the core library
	uv pip install --system -e ${ENGINE_DIR}

install-quality: ${ENGINE_DIR} ${PYPROJECT_CONFIG_FILE} ## Install with quality dependencies
	uv pip install --system -e '${ENGINE_DIR}[quality]'

lint-check: ${PYPROJECT_CONFIG_FILE} ## Check code formatting and linting
	ruff format --check . --config ${PYPROJECT_CONFIG_FILE}
	ruff check . --config ${PYPROJECT_CONFIG_FILE}

lint-format: ${PYPROJECT_CONFIG_FILE} ## Format code and fix linting issues
	ruff format . --config ${PYPROJECT_CONFIG_FILE}
	ruff check --fix . --config ${PYPROJECT_CONFIG_FILE}

precommit: ${PYPROJECT_CONFIG_FILE} .pre-commit-config.yaml ## Run pre-commit hooks
	pre-commit run --all-files

typing-check: ${PYPROJECT_CONFIG_FILE} ## Check type annotations
	ty check . --project ${ENGINE_DIR}

deps-check: .github/verify_deps_sync.py ## Check dependency synchronization
	uv run .github/verify_deps_sync.py

# this target runs checks on all files
quality: lint-check typing-check deps-check ## Run all quality checks

style: lint-format precommit ## Format code and run pre-commit hooks

########################################################
# Tests
########################################################


########################################################
# Setup GitHub
########################################################

# Clone GH labels
init-gh-labels: ## Initialize GitHub labels
	gh label clone frgfm/fastemplate --repo ${REPO_OWNER}/${REPO_NAME} --force

# GitHub repo settings
init-gh-settings: ## Configure GitHub repository settings
	gh repo edit ${REPO_OWNER}/${REPO_NAME} \
		--delete-branch-on-merge
		--enable-squash-merge
		--enable-rebase-merge=false
		--enable-merge-commit=false

########################################################
# Mintlify docs
########################################################

install-mintlify: ## Install Mintlify globally
	pnpm i -g mint

start-mintlify: ## Start Mintlify development server
	cd ${DOCS_DIR} && mint dev
