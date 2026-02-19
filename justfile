# Run the full scraping and analysis pipeline
all: scrape-all

# Perform an initial full scrape of all suburbs
scrape-all:
    uv run -- main.py

# Perform a daily update scrape for the latest listings
scrape-daily:
    uv run -- daily.py

# Handle suburbs that were skipped due to having too many results
scrape-missed:
    uv run -- missed.py

# Run all quality checks (linting, formatting, type checking)
check:
    uv run -- prek run -a
