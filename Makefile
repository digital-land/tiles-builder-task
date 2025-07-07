.PHONY: task test

clean:
	@rm -rf ./files


test-integration:
	python -m pytest tests/integration

test-e2e:
	python -m pytest tests/e2e

test: test-integration test-e2e

lint:
	black .
	flake8 .

# for development not for docker
init:
	python -m pip install pip-tools
	python -m piptools sync requirements/dev-requirements.txt
	python -m pre_commit install

# for easy running
task:
	./build.sh
