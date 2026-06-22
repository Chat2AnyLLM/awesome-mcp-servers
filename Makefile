.PHONY: validate build ci clean install update-readme all test

install:
	pip install -r requirements.txt

validate:
	python scripts/validate.py

build:
	python scripts/build.py

test:
	python -m unittest discover -s tests -v

update-readme:
	python scripts/update_readme.py

ci: validate test build

all: validate test build update-readme

clean:
	rm -rf dist/ scraped/
