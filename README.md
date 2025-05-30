
# projectalpha
## Before doing anything
> **Note:** If you don't have PYTHON3 installed, please install it first(DUH!).

## Running Django server
### FIRST AND FOREMOST
```bash
pip install -r requirements.txt
```
### Starting the server
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Running OpenSearch in Docker

To run OpenSearch using Docker, use the following command:

```bash
docker run -it -p 9200:9200 -p 9600:9600 \
  -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=B0unT@Adm7 \
  -e "discovery.type=single-node" \
  --name opensearch-node \
  opensearchproject/opensearch:latest
```

## Starting the UI

> **Note:** If you don't have NVM (Node Version Manager) installed, please install it first.

Install Node.js version `22.16.0` using NVM and follow the steps:
   ```bash
   nvm install 22.16.0
   nvm use 22.16.0
   npm install
   npm run dev
   ```
