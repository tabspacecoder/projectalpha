
# projectalpha

## Running OpenSearch in Docker

To run OpenSearch using Docker, use the following command:

```bash
docker run -it -p 9200:9200 -p 9600:9600 \
  -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=B0unT@Adm7 \
  -e "discovery.type=single-node" \
  --name opensearch-node \
  opensearchproject/opensearch:latest
## To start the UI
*Note - if you don't have NVM please install it
step 1 : Install node v14.21.3
Step 2 : npm Install
Step 3 : npm run dev
```

## Starting the UI

> **Note:** If you don't have NVM (Node Version Manager) installed, please install it first.

Install Node.js version `14.21.3` using NVM and follow the steps:
   ```bash
   nvm install 14.21.3
   nvm use 14.21.3
   npm install
   npm run dev
   ```
