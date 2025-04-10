format:
	black .
	isort .
lint:
	flake8 .
test:
	python -m pytest test/ --verbose


