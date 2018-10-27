# Determine this makefile's path.
# Be sure to place this BEFORE `include` directives, if any.
# source: https://stackoverflow.com/a/27132934/7331040
THIS_FILE := $(lastword $(MAKEFILE_LIST))
MANAGE = python paguen_po/manage.py


# target: all - Default target. Does nothing.
all:
	@echo "Hello $(LOGNAME), nothing to do by default.";
	@echo "Try 'make help'.";

# target: build - Builds the project using 'production' settings.
build:
	pip install -r requirements/dev.txt;
	$(MANAGE) migrate;
	$(MANAGE) collectstatic --no-input;


# target: help - Display callable targets.
help:
	@echo "These are common commands used in various situations:\n";
	@grep -E "^# target:" [Mm]akefile;

# target: run - Runs dev server. You can pass additional arguments with ARGS parameter, eg: 'make run ARGS=9000'.
run:
	$(MANAGE) runserver 0.0.0.0:8000


# target: shell - Opens django shell.
shell:
	$(MANAGE) shell_plus || $(MANAGE) shell;
