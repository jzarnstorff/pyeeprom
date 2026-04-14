# PyEEPROM

## Developer Requirements

`Poetry` is used to manage the project's dependencies and can be installed using the installer directly from [install.python-poetry.org](https://install.python-poetry.org/). The script can be executed directly using `curl` and `python` from your Linux environment.

    curl -sSL https://install.python-poetry.org | python3 -

After successfully installing `Poetry`, install the project's dependencies:

    poetry install --with dev,docs

Source the virtual environment:

    source .venv/bin/activate

Install `pre-commit` to set up the git hook scripts to run linters on the source code when making commits. More information on `pre-commit` can be found at [pre-commit.com](https://pre-commit.com/)

    pre-commit install
