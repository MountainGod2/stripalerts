on: [push]

jobs:
  ruff:
    runs-on: ubuntu-latest
    name: "ruff"
    steps:
      - uses: davidslusser/actions_python_ruff@v1.0.0
