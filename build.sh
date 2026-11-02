#!/usr/bin/env bash
# Render runs this script to build the app before starting it.
# `errexit` stops at the first command that fails, so a broken build never goes live.
set -o errexit

# Install uv if the build machine doesn't have it yet.
command -v uv >/dev/null 2>&1 || pip install uv

# Exact versions from uv.lock, without the development tools (tests, Ruff...).
uv sync --frozen --no-dev

uv run --no-dev python manage.py tailwind build            # compile the CSS
uv run --no-dev python manage.py collectstatic --no-input  # gather static files
uv run --no-dev python manage.py migrate --no-input        # update the database
uv run --no-dev python manage.py load_questions            # add any new questions
