SHELL := /bin/bash
PYTHON := python
PIP := pip

deps:
	pip install -U -t lib --no-deps -r requirements.txt
