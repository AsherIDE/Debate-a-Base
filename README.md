# Version 2.0
Welcome to the *debate-a-base website repository*, this website runs on Flask with a Docker instance of Elasticsearch running in the background. Further requirements to run this website can be found in the `requirements.txt` file.

# Launch testing server
### Venv selection
- Set-ExecutionPolicy Unrestricted -Scope Process 
- .\venv\Scripts\Activate

### Venv starting
- flask run --host 0.0.0.0 --port 5000