# AT3-Group30-experiments

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Shared experimentation repository for Group 30's cryptocurrency financial
intelligence platform. It contains reproducible data preparation, feature
engineering, target construction, modelling, Optuna optimisation and evaluation.

## Student B: Market Risk Index

Student B develops a LightGBM regression model that forecasts the Market Risk
Index (MRI) seven days ahead. The model uses Return20, Volatility20, MaxPrice20
and Gap Risk. Student B owns and exposes MA5, MA20 and TrendStrength.

## Reproducible setup

1. Install Python 3.12.13 and create a virtual environment.
2. Run `pip install -r requirements.txt`.
3. Place the supplied token folders under `data/raw/coinmarketcap/`.
4. Run `python -m at3_group30_experiments.dataset`.

This produces `data/processed/cryptocurrency_daily.csv` and the tracked audit
`reports/data_quality.json`. Empty pre-launch files are documented and skipped;
overlapping observations must agree; missing dates are reported but never filled.

Run automated checks with `python -m pytest -q`.

## Group details

- Group: 30
- Student A: add name and student ID before submission
- Student B: Nipun Mudgal — add student ID before submission
- Student C: add name and student ID before submission
- Student D: add name and student ID before submission

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         at3_group30_experiments and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── at3_group30_experiments   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes at3_group30_experiments a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------
