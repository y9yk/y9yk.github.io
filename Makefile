.DEFAULT_GOAL := help
PYTHON ?= python3
PORT ?= 8000
.PHONY: help build check serve dev preview
help:
	@printf '%s\n' 'make serve    Build and preview at http://127.0.0.1:$(PORT)' 'make build    Build approved public pages' 'make check    Run checks' 'Use PORT=8001 to select another port. Stop with Ctrl+C.'
build:
	$(PYTHON) scripts/build.py
check:
	$(PYTHON) -m unittest discover -s tests -v
	node --check assets/site.js
	node --check assets/analytics.js
	node --check assets/stats.js
	node --check assets/stats-story.js
	node --test tests/*.test.cjs
serve: build
	@printf '\nPreview: http://127.0.0.1:$(PORT)\nStop with Ctrl+C.\n\n'
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory dist
dev preview: serve
