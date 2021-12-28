install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

# run:
# 	python manage.py runserver

# test:
# 	python -m pytest -vv --cov=mylib test_mathcode.py

# lint:
# 	pylint --disable=R,C mylib cli

# all: install lint test