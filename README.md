# Domain Webscraper

A webscraper that searches [domain.com.au](https://www.domain.com.au) for sold properties.

## Features

- Scrapes sold property data including price, address, features (beds, baths, parking), and sold dates.
- Uses Selenium with Firefox in headless mode.
- Supports comprehensive scraping (`main.py`), daily updates (`daily.py`), and re-attempting missed suburbs (`missed.py`).
- Includes a data analysis script (`analysis.py`) for property price prediction models.

## Modernized Tech Stack

- **Package Management**: Managed by [uv](https://github.com/astral-sh/uv).
- **Linting & Formatting**: [Ruff](https://github.com/astral-sh/ruff).
- **Type Checking**: [ty](https://github.com/dtandersen/ty) (based on Pyright).
- **Automation**: Pre-commit hooks for quality assurance.

## Installation

1. Install `uv`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Sync dependencies:
   ```bash
   uv sync
   ```

3. Ensure Firefox and [Geckodriver](https://github.com/mozilla/geckodriver/releases) are installed on your system.

## Usage

### Web Scraper

- **Initial/Full Scrape**:
  ```bash
  uv run main.py
  ```
- **Daily Updates**:
  ```bash
  uv run daily.py
  ```
- **Missed Suburbs**:
  ```bash
  uv run missed.py
  ```

### Data Analysis

Run the analysis script to process the scraped data and test various regression models:
```bash
uv run analysis.py
```

## Quality Control

The project is configured with `ruff` and `ty`. You can run checks manually:
```bash
uv run ruff check .
uv run ty check
```
Or run all pre-commit hooks:
```bash
uv run pre-commit run -a
```
