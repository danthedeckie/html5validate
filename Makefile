test:
	python -m unittest

autotest:
	find . -name \*.py -not -path .\/.v\* | entr make test

.PHONY: test

dist/: setup.py html5validate.py README.rst
	python setup.py build sdist
	twine check dist/*

pypi: test dist/
	twine check dist/*
	twine upload dist/*

clean:
	rm -r build
	rm -r dist
