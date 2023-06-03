.venv/bin/python:
	python3 -m venv .venv

.venv/.install.stamp: .venv/bin/python requirements.txt requirements-dev.txt
	.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
	touch .venv/.install.stamp

update-deps: .venv/bin/python
	pre-commit autoupdate
	python -m pip install --upgrade pip-tools pip wheel
	python -m piptools compile --upgrade --resolver backtracking -o requirements.txt pyproject.toml
	python -m piptools compile --extra dev --upgrade --resolver backtracking -o requirements-dev.txt pyproject.toml
	python -m pip check

compile-deps: .venv/bin/python
	python -m piptools compile --resolver backtracking -o requirements.txt pyproject.toml
	python -m piptools compile --extra dev --resolver backtracking -o requirements-dev.txt pyproject.toml

init: .venv/.install.stamp
	pre-commit install

test: .venv/.install.stamp
	.venv/bin/python app/manage.py test app

.PHONY: update-deps compile-deps init test
