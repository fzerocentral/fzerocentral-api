# fzerocentral-api

Data API for the (upcoming) F-Zero Central website. Uses the Django web framework.


## Installation for development environments

- Ensure you have the following installed:
  - Python 3.10.x
  - PostgreSQL 10 or higher (see below section for a sample PostgreSQL setup)
  - On Ubuntu, the following apt packages: `python3.10-dev`, `python3.10-venv`, `libpq-dev`
- `git clone` this repository.
- Set up a virtual environment and install Python packages there:
  - Create a virtual environment at the directory of your choice (can be outside of the repository): `python3.10 -m venv <path/to/environment>`
  - Activate your environment: `source <path/to/environment>/bin/activate` on Linux, `<path/to/environment>/Scripts/activate` on Windows.
  - If on Linux, run `pip install wheel`
  - Run `pip install -r requirements/development.txt` to install packages to your environment. Ensure that there are no installation errors.
- Create an `.env` file at the root of this repository. Specify configuration variable values in this file, using the `.env.dist` file as a template.
- Set an environment variable to specify you're using the 'development' settings module. `export DJANGO_SETTINGS_MODULE=config.settings.development` on Linux, `set DJANGO_SETTINGS_MODULE=config.settings.development` on Windows.
- Run `python manage.py migrate` to create the database schema.

## Sample PostgreSQL setup (Ubuntu)

- `sudo apt install postgresql`
- `sudo -u postgres psql` to enter the psql shell with the newly-created Linux user `postgres`, which is tied to the default PostgreSQL user `postgres`.
- On the psql shell:
  - `CREATE USER django WITH PASSWORD 'mypassword';` replacing mypassword with the DATABASE_PASSWORD set in your `.env` file.
  - `ALTER ROLE django SET client_encoding TO 'utf8';` - this and the following two commands are for [optimizing Django's connections to PostgreSQL](https://docs.djangoproject.com/en/dev/ref/databases/#optimizing-postgresql-s-configuration).
  - `ALTER ROLE django SET default_transaction_isolation TO 'read committed';`
  - `ALTER ROLE django SET timezone TO 'UTC';`
  - `CREATE DATABASE mydatabase;` replacing mydatabase with your DATABASE_NAME.
  - `GRANT ALL PRIVILEGES ON DATABASE mydatabase TO django;`
  - `\q` to exit the psql shell.
- If you've got your Python environment all set up, you can run `python manage.py dbshell` to test entering the psql shell through Django's settings. Then run `\c` on the psql shell to confirm the user and database names.

## Running the development server

- Set the environment variable to specify your settings module (see above).
- Activate your virtual environment (see above).
- From the `project` directory, run: `python manage.py runserver`
  - You can specify a port number after `runserver` to serve the API at that port.
- The website should be served at your localhost address. For example, if it's `127.0.0.1:8000`, try visiting `http://127.0.0.1:8000/games` in your browser.

## Running the unit tests

- Set the environment variable to specify your settings module (see above).
- Activate your virtual environment (see above).
- From the `project` directory, run: `python manage.py test`

## Miscellaneous developer tips

- When using the PyCharm IDE, if many import statements such as `from games.models import Game` are getting red-underlined, try right-clicking the `project` directory, and choose Mark Directory as -> Sources Root. 
- Firefox may not know how to display responses of the content type `application/vnd.api+json`. One add-on that can help with this is [JSON Lite](https://github.com/lauriro/json-lite).
