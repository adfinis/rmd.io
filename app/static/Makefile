SHELL:=/bin/bash

.PHONY: help

help:
	@echo "Sass to css converter"
	@echo
	@echo "run \"make css\""
	@echo "or \"make watch\""

css: sass/style.sass
	sass sass/style.sass style.css

watch: sass/style.sass
	sass --watch sass/style.sass:style.css
