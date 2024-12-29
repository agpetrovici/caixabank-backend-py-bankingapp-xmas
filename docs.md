Export pyproject.toml to requirements.txt
`poetry export -f requirements.txt --output requirements.txt`

then
<!-- builds docker image, we have to run this to ensure that the libraries are installed
`docker build -t caixabank .` -->

runs docker compose, this will run the app
`docker compose up -d --build`