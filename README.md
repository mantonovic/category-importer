# Open Food Facts - Food Category importer

This project is a tool to import food categories from Open Food Facts into a local PostgreSQL database with an `ltree` column. ~~It is designed to be run manually or as a scheduled task to keep the local database up-to-date with the latest food categories from Open Food Facts.~~

## Features

1. Fetches food categories from Open Food Facts API.
2. Check if the food category tables exist in the local PostgreSQL database, and creates them if they do not, uses the [schema.sql](./db/1-DB-SCHEMA.sql) file for the database schema.
~~3. If the tables already exist, it checks for new food categories and updates the database accordingly.~~
4. Logs the import process for monitoring and debugging purposes.

## Prerequisites

Prepare the `.env` file with the following content, replacing the values with your actual database credentials:

```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=database_name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Using Docker

Build the Docker image:

```bash
DOCKER_BUILDKIT=1 \
docker build \
    -t category-importer:latest \
    -f Dockerfile .
```

Tag the Docker image:

```bash
docker tag \
    category-importer:latest \
    https://github.com/mantonovic/category-importer:latest
```

## Using venv

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage


### Using venv:

Remember to activate the virtual environment before running the commands:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Run all steps with one command:

### Using venv:

```bash
python src/category.py run-all
```

### Using Docker:

```bash
docker run --rm -it  \
    --network=host \
    --env-file .env \
    category-importer:latest
        python src/category.py run-all
```

Run steps manually:

1. Fetch off_category JSON in `data/`:



```bash
python src/category.py fetch
```

Using Docker:

```bash
docker run --rm -it  \
    --network=host \
    --env-file .env \
    category-importer:latest
        python src/category.py fetch
```

2. Initialize DB schema if tables are missing:

```bash
python src/category.py init-db
```

Using Docker:

```bash
docker run --rm -it  \
    --network=host \
    --env-file .env \
    category-importer:latest
        python src/category.py init-db
```

3. Import off_category into PostgreSQL:

```bash
python src/category.py import
```


Using Docker:

```bash
docker run --rm -it  \
    --network=host \
    --env-file .env \
    category-importer:latest
        python src/category.py import
```

You can still run each script directly if needed:

```bash
python src/fetch_off_category.py
python src/init_db.py
python src/import_off_category.py
```
