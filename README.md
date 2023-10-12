# Launch testing server
### Venv selecteren
- Set-ExecutionPolicy Unrestricted -Scope Process 
- .\venv\Scripts\Activate

### Venv starten
- flask run --host 0.0.0.0 --port 5000
- Updaten with: docker compose build --> docker compose up -d

# Publishing
### Import requirements
- pip freeze > requirements.txt

### Docker setup
- https://tecadmin.net/how-to-create-and-run-a-flask-application-using-docker/
- Docker up --> docker run -it -p 5000:5000 -d website
    - Random code die docker gaf: 6636a461ba1f90433c127c59551cf57d0a165fdc602c2ea30cf27d57e03b3cf1

### Opload image
- docker build . -t git.kallestruik.nl/asher/debate_a_base:2.0
- docker tag git.kallestruik.nl/asher/debate_a_base:2.0 git.kallestruik.nl/asher/debate_a_base:latest
- docker push git.kallestruik.nl/asher/debate_a_base:2.0
- docker push git.kallestruik.nl/asher/debate_a_base:latest

### Finding the esdata location folder
- Double "\\" at the start
- "\\\wsl$\docker-desktop-data\data\docker\volumes"

# Deployment
1. Place `docker-compose.yml` and `.env` in the deployment directory.
2. Unzip the `esdata.zip` file into the same folder. This should leave you with the following structure:
```sh
[ROOT]
|- docker-compose.yml
|- .env
|- esdata
   |- {Elastic search files}
```
3. Run `docker-compose pull` to pull latest versions of all images.
4. Run `docker-compose up -d` to start the stack.
5. The website is now available at `0.0.0.0:5000`.