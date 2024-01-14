# Github action for running python linting with ruff 

name: Ruff linter

on:
  push:
    branches: [ "master" ]
  pull_request:
    branches: [ "master" ]

jobs:
  ruff:
    runs-on: ubuntu-latest
    name: "ruff"
    steps:
      - uses: davidslusser/actions_python_ruff@v1.0.0
