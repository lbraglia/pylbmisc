test:
	pytest

flake8:
	flake8

doc-refresh:
	sphinx-apidoc -f src/pylbmisc -o docs

mypy:
	mypy .

black:
	black --line-length 79 .
