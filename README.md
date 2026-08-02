# Artificial Axon Lab Pipeline

The Tkinter frontend collects upload, settings, and masking configuration. FastAPI runs in Docker, performs the Fiji/ImageJ analysis, and stores the final CSV files and job history in PostgreSQL.

## Docker analysis setup

2. Edit `.env`:

```env
AXONLAB_DATA_ROOT=C:/path/to/the/shared/microscope/data
```

The data root is mounted writable at `/data`. Fiji and the required MCIB3D jars are installed in the Docker image at `/opt/fiji`. Every folder selected in the frontend must be inside `AXONLAB_DATA_ROOT`.

3. Start the application from the project directory:

```powershell
.\start.ps1
```

The launcher installs only the lightweight dependencies needed by the local Tkinter frontend. Docker installs Java, PyImageJ, SciJava, FastAPI, and all server dependencies while building the API image.

On the Results page, **Run Analysis** creates a FastAPI analysis job. The frontend polls the job while the API container runs masking, object measurement, and consolidation. The completed CSV is saved in PostgreSQL and displayed on the Results page.

Useful commands:

```powershell
docker compose up -d --build
docker compose logs -f api
docker compose down
```

API documentation is available at <http://127.0.0.1:8000/docs>.
