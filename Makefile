.DEFAULT_GOAL := help

help: ## show this help message
	@echo
	@echo "    ____  __                  _                ____        __       "
	@echo "   / __ \/ /___ _____  ____  (_)___  ____ _   / __ \____ _/ /_____ _"
	@echo "  / /_/ / / __ \`/ __ \/ __ \/ / __ \/ __ \`/  / / / / __ \`/ __/ __ \`/"
	@echo " / ____/ / /_/ / / / / / / / / / / / /_/ /  / /_/ / /_/ / /_/ /_/ / "
	@echo "/_/   /_/\__,_/_/ /_/_/ /_/_/_/ /_/\__, /  /_____/\__,_/\__/\__,_/  "
	@echo "                                  /____/                            "
	@echo
	@echo "Usage: make <action>"
	@echo
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo

.PHONY: help clean init task docker-task serve docker-serve test test-acceptance

PORT ?= 8080

clean: ## remove generated tiles and downloaded geojson
	@rm -rf ./tiles ./cache

init: ## install dev requirements and pre-commit hooks (must be run inside an activated virtual environment)
	@python -c 'import sys; sys.exit(sys.prefix == sys.base_prefix)' || (echo "not in a virtual environment, create and activate one first: python -m venv .venv && source .venv/bin/activate" && exit 1)
	python -m pip install -r requirements/dev.txt
	python -m pre_commit install

task: ## build tiles locally with tippecanoe, e.g. make task DATASET=central-activities-zone
	./build.sh

docker-task: ## build tiles in docker, e.g. make docker-task DATASET=central-activities-zone
	@test -n "$(DATASET)" || (echo "DATASET must be set, e.g. make docker-task DATASET=central-activities-zone" && exit 1)
	DATASET=$(DATASET) UID=$$(id -u) GID=$$(id -g) docker compose run --rm --build tiles-builder

serve: ## serve ./tiles locally with python at http://localhost:8080 (override with PORT=...)
	@test -d ./tiles || (echo "no ./tiles directory, build some tiles first with make task or make docker-task" && exit 1)
	python scripts/serve.py --port $(PORT)

docker-serve: ## serve ./tiles in docker with nginx at http://localhost:8080 (override with PORT=...)
	@test -d ./tiles || (echo "no ./tiles directory, build some tiles first with make task or make docker-task" && exit 1)
	PORT=$(PORT) docker compose up tiles-server

test: test-acceptance ## run all tests

test-acceptance: ## run the acceptance tests against the docker image (needs docker)
	python -m pytest tests/acceptance
