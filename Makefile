ENGINE_DIR = ./relay
CLI_DIR = ./cli
DOCS_DIR = ./docs
ENGINE_CONFIG_FILE = ${ENGINE_DIR}/pyproject.toml
CLI_CONFIG_FILE = ${CLI_DIR}/pyproject.toml
PYTHON_REQ_FILE = /tmp/requirements.txt

########################################################
# Code checks
########################################################

install-engine: ${CORE_DIR} ${ENGINE_CONFIG_FILE}
	uv pip install --system -e ${CORE_DIR}

install-cli: ${CLI_DIR} ${CLI_CONFIG_FILE}
	uv pip install --system -e ${CLI_DIR}

install-quality: ${CORE_DIR} ${ENGINE_CONFIG_FILE}
	uv pip install --system -e '${CORE_DIR}/.[quality]'

lint-check: ${ENGINE_CONFIG_FILE}
	ruff format --check . --config ${ENGINE_CONFIG_FILE}
	ruff check . --config ${ENGINE_CONFIG_FILE}

lint-format: ${ENGINE_CONFIG_FILE}
	ruff format . --config ${ENGINE_CONFIG_FILE}
	ruff check --fix . --config ${ENGINE_CONFIG_FILE}

precommit: ${ENGINE_CONFIG_FILE} .pre-commit-config.yaml
	pre-commit run --all-files

typing-check: ${ENGINE_CONFIG_FILE}
	ty check . --config ${ENGINE_CONFIG_FILE}

deps-check: .github/verify_deps_sync.py
	uv run .github/verify_deps_sync.py

# this target runs checks on all files
quality: lint-check typing-check deps-check

style: lint-format precommit



########################################################
# Tests
########################################################


########################################################
# Setup GitHub
########################################################

# Clone GH labels
init-gh-labels:
	gh label clone frgfm/fastemplate --repo ${REPO_OWNER}/${REPO_NAME} --force

# GitHub repo settings
init-gh-settings:
	gh repo edit ${REPO_OWNER}/${REPO_NAME} \
		--delete-branch-on-merge
		--enable-squash-merge
		--enable-rebase-merge=false
		--enable-merge-commit=false

########################################################
# Mintlify docs
########################################################

install-mintlify:
	pnpm i -g mint

start-mintlify:
	cd ${DOCS_DIR} && mint dev
