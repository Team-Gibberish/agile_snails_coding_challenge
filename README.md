# CodingChallenge

[![Python Tests](https://github.com/Agile-Snails/CodingChallenge/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/Agile-Snails/CodingChallenge/actions/workflows/main.yml)

AIMLAC Coding Challenge

## Aims & Objectives

- Predict on site power generation at 30 minute intervals for at least the next 24 hours. The National Grid charges a penalty fee for any power generator who over estimates their power output and is unable to deliver.
- Automatically decide upon a price to sell any excess electricity to the National Grid. The price must be as profitable as possible while still being competitive with the general wholesale market. This must be specified at 30 minute intervals.
- Produce a regular report for management stating:
	- Revenue from selling electricity
	- Cost of imported electricity
	- Cost savings compared to buying from the National Grid at a rate of 15 pence per kilowatt hour
	- Carbon dioxide savings compared to buying from the National Grid. *Note that the carbon intensity of the grid varies.*

## Installation

Currently, only building and installing from source is available.


## Installing the anaconda environment

The conda environment is defined in [environment.yml](./environment.yml)

- To create an environment use `conda env create ./environment.yml`
	- This will automatically install all the dependencies to the `sjautobidder`
		environment.
- Activate the environment with `conda activate sjautobidder`
- To delete an environment, use `conda env remove -n envname`

## Building the frontend

For details about the frontend, see [webpage/README.md](./webpage/README.md)

## Installing the package

> This would be used for deployment, but does not have a use while developing.
> Infact, installing the module might break testing with conflicted imported
> modules.

```bash
"conda activate sjautobidder;",
"python -m build .;",

# Optionally install with pip. --force-reinstall ensures it is installed
# even if the version has not been bumped.
"python -m pip install .\\dist\\sjautobidder-0.0.1-py3-none-any.whl --force-reinstall",
```

The distributable module is outputted to the `dist/` folder, in both
pip-installable `.whl` format and as a compressed `.tar.gz` folder.

## Docker-compose

To start the docker container, make sure you have run the steps under [Installing the package](##Installing-the-package), then navigate to the root of the project and run:

```bash
docker build -t codingchallenge .
docker run -dp 80:80 codingchallenge
```

## Linting

To lint the project:

- Activate the environment with `conda activate sjautobidder`
- Run the command `prospector . -s high`
- Also check comment style by running `pydocstyle`

## Testing

To test the project:

- Activate the environment with `conda activate sjautobidder`
- Run the command `pytest .`

To generate a coverage report:

- For a terminal coverage report:
	- Use `pytest . --cov-report term --cov=sjautobidder tests/`

		```bash
		----------- coverage: platform win32, python 3.8.8-final-0 -----------
		Name                                               Stmts   Miss  Cover
		----------------------------------------------------------------------
		sjautobidder\building_demand\__init__.py               0      0   100%
		sjautobidder\building_demand\energy_demand.py         31     13    58%
		sjautobidder\building_demand\energy_utils.py          24      0   100%
		sjautobidder\met_office_api\__init__.py                0      0   100%
		sjautobidder\met_office_api\api_interpolation.py      11     11     0%
		sjautobidder\met_office_api\api_utils.py             114    114     0%
		sjautobidder\solar_power\__init__.py                   0      0   100%
		sjautobidder\solar_power\solar_power.py               44     44     0%
		sjautobidder\solar_power\solar_utils.py               27     18    33%
		----------------------------------------------------------------------
		TOTAL                                                251    200    20%
		```

- To generate a cov.xml for IDE extensions:
	- Use `pytest --cov-report xml:cov.xml --cov=sjautobidder tests/`


# Contributing

When committing code that may effect more than just your owned files, please
open a pull request instead and tag the writer of the code you changed.

We use black as our formatting guide, and is recommended you run the formatter
on your code before committing.

For doc comments, each function must be commented alongside a top-level module
comment. The standard we have adopted is the [Google Standard](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
Note that incorrect docs will be picked up as the linter and reported as errors.
Please run the linter before committing!

Github actions will run pytest and linting on pull requests and commits, so
pleasure be sure that your code conforms!

## Pre-commit check list

- [ ] Use black formatter on your code.
- [ ] Run Pytest to ensure tests pass.
- [ ] Use the linter to ensure standards are followed, along with correct comments.
- [ ] If changing someone else's files, issue a pull request instead.
