# UnTube Docker

Dockerfile and docker-compose file to try the [UnTube](https://github.com/sleepytaco/UnTube) web application.

Untube is a simple and comprehensive YouTube playlist management web application powered by the YouTube V3 data API, created by [sleepytaco](https://github.com/sleepytaco) using Django, htmx and Bootstrap.

## Prerequisites
- Docker must be installed on the host machine.
- Docker-compose must also be installed if you want to deploy the application via the docker-compose file.

## Usage
Import the project, and enter to the following directory:
```bash
git clone https://github.com/noelaridan/UnTube-Docker.git
cd UnTube-Docker
```
Edit the `ALLOWED_HOSTS` in `webapp/UnTube/settings.py`
```bash
nano webapp/UnTube/settings.py
```
Add a domain name to be able to connect via the YouTube API.

For example:
```
ALLOWED_HOSTS = ['127.0.0.1', 'your-domain.com']
```
Then change the `YOUTUBE_V3_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` in the `webapp/UnTube/secrets.py` file.

For example:
```
# Make sure you change these before production or to run this project on your own machine ;)
SECRETS = {"SECRET_KEY": 'django-insecure-ycs22y+20sq67y(6dm6ynqw=dlhg!)%vuqpd@$p6rf3!#1h$u=',
           "YOUTUBE_V3_API_KEY": 'your-youtube-api-key',
           "GOOGLE_OAUTH_CLIENT_ID": "your-oauth-client-id",
           "GOOGLE_OAUTH_CLIENT_SECRET": "your-oauth-client-secret",
           "GOOGLE_OAUTH_SCOPES": ['https://www.googleapis.com/auth/youtube']}
```
## Using docker run
Build the docker image:
```bash
docker build -t untube .
```
Then enter the following command to start the container by changing the path of the sqlite file:
```bash
docker run -d -p 8000:8000 -v /{absolute-path}/db/db.sqlite3:/app/db.sqlite3 untube
```
Finally, type in your search engine, the address corresponding to the one in the `settings.py` file.
## Using docker-compose (recommended)
Enter the following command to start the container:
```bash
docker-compose up -d
```
Finally, Type in your search engine, the address corresponding to the one in the `settings.py` file.
