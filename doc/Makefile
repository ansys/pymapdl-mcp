# Makefile for Sphinx documentation

# You can set these variables from the command line.
SPHINXOPTS    ?= -W --keep-going
SPHINXBUILD   ?= sphinx-build
PAPER         ?=
BUILDDIR      ?= _build

# The `sed` command below replaces underscores with spaces.
# Additionally, the output is converted to lowercase.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source
SPHINX_LANG     ?=

# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source

.PHONY: help clean html

help:
	@$(SPHINXBUILD) -M help "$(CURDIR)" "$(BUILDDIR)" $(ALLSPHINXOPTS) $(O)

clean:
	rm -rf $(BUILDDIR)/*

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

pdf:
	@echo "No PDF documentation build available..."
	touch $(BUILDDIR)/ansys-mapdl-mcp.pdf

.DEFAULT_GOAL := help
