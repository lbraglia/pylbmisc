test:
	pytest

lint:
	flake8

doc-refresh:
	sphinx-apidoc -f src/pylbmisc -o docs

mypy:
	mypy .

black:
	black .
