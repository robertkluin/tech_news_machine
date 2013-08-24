SHELL := /bin/bash
PYTHON := python
PIP := pip

BASE_DIR := $(shell python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")

deps:
	pip install -Ur requirements.txt
	ln -s $(BASE_DIR)/furious lib
	ln -s $(BASE_DIR)/BeautifulSoup.py lib
	ln -s $(BASE_DIR)/feedparser.py lib
