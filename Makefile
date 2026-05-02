# Set default target
.DEFAULT_GOAL := help

dir = $(shell pwd)

help:
	@echo "Usage: make [help]"
	@echo "help: show this help message"
