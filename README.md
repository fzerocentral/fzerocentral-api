# fzerocentral-api-django

Data API for the (upcoming) F-Zero Central website. Uses the Django web framework.


## Installation for development environments

- `git clone` this repository.
- Install the latest Python 3.10.x.
- Install the latest PostgreSQL.
  - Create a user `django`, and create a database `fzerocentral`, which grants full permissions to the user you created. You can also use different names, as long as you specify those names in the `.env` file described later.
- Set up a virtual environment and install Python packages there:
  - Create a virtual environment at the directory of your choice (can be outside of the repository): `python -m venv <path/to/environment>`
    - If your system has multiple Python installations, be sure to use the `python` executable from the correct installation.
  - Activate your environment: `source <path/to/environment>/bin/activate` on Linux, `<path/to/environment>/Scripts/activate` on Windows.
  - Run `pip install -r requirements/development.txt` to install packages to your environment. Ensure that there are no installation errors.
- Create an `.env` file at the root of this repository. Specify configuration variable values in this file, using the `.env.dist` file as a template.
- Set an environment variable to specify you're using the 'development' settings module. `export DJANGO_SETTINGS_MODULE=config.settings.development` on Linux, `set DJANGO_SETTINGS_MODULE=config.settings.development` on Windows.
- Run `python manage.py migrate` to create the database schema.

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
