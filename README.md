# Artificial Axon Lab Pipeline 

The Tkinter frontend collects upload, settings, and masking configuration. FastAPI runs in Docker, performs the Fiji/ImageJ analysis, and stores the final CSV files and job history in PostgreSQL.

## Download and run Docker Desktop
1. Download and install Docker Desktop from <https://www.docker.com/products/docker-desktop/>. 

2. To run the pipeline, you need to have Docker Desktop running, so enter the command: 
```
docker desktop start -d
```


## Start the Tkinter Application
from the project directory, run the following command to start the application:

for windows:
```
.\start.ps1
```
for macOS/Git Bash:
```
./start.sh
```

* If you are in a virtual environment CLI, you may need to run the command with `deactivate` first to exit the virtual environment.

<br>

## View the FastAPI documentation
Fast API documentation is available at <http://127.0.0.1:8000/docs>.
* Health API availability check code 200 means FastAPI is running.