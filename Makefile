test:
	pytest

flake8:
	flake8
	# flake8 --ignore=E501

doc-refresh:
	sphinx-apidoc -f src/pylbmisc -o docs

mypy:
	mypy .

black:
	black --line-length 79 . # make it coherent with flake E501
