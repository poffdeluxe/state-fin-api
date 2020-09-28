# state-fin-api
API for retrieving finance information regarding state legislature campaigns

This repo is the sister project of [state-fin-ingest](https://github.com/poffdeluxe/state-fin-ingest). This API aggregates and retreives finance information related to state legislature campaigns from an Elasticsearch cluster. The state-fin-ingest project ingests and stores the data in ES and this state-fin-api retrieves it.

At the moment, information is limited to contribution transactions. Information regarding expenses, loans, etc is planned for the future.

## Getting started
To get started, you need to have a .env file in the root directory with the `ES_HOST` variable that has the full path to the Elasticsearch cluster (including authentication).

You'll also need `poetry` installed on your local machine.

Running `poetry install` will install the dependencies.

To start the server, run `poetry run uvicorn main:app --reload`

Thanks to FastAPI, this API is automatically self-documenting. You can view the API docs by starting the server and navigating to http://127.0.0.1/docs
An OpenAPI endpoint is also provided.

## Demo
A demo instance is currently running on Heroku at: https://state-fin-api.herokuapp.com
At the moment, the demo instance only has data for the state of Texas