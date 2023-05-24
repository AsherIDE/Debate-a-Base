### Venv selecteren
- Set-ExecutionPolicy Unrestricted -Scope Process 
- .\venv\Scripts\activate

### Venv starten (Keus uit 2)
- flask run --host 0.0.0.0 --port 5000
- Updaten met: docker compose build --> docker compose up -d

### Import requirements
- pip freeze > requirements.txt

### Docker setup
- https://tecadmin.net/how-to-create-and-run-a-flask-application-using-docker/
- Docker up --> docker run -it -p 5000:5000 -d website
    - Random code die docker gaf: 6636a461ba1f90433c127c59551cf57d0a165fdc602c2ea30cf27d57e03b3cf1