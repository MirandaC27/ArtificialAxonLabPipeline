# AxonLabPipeline

download either of these files:

Windows: pipeline.exe
Mac: pipeline.dmg

run it how you would any desktop app.

# Desktop version aren't working and you need to run this raw:
things about running:
You need a virtual environment. Make it with these:
conda create -n NAME OF ENVIRONMENT HERE -c conda-forge python=3.10 pyimagej openjdk=11 maven opencv numpy scipy pandas pytest pytest-cov
conda activate NAME OF ENVIRONMENT HERE

conda install -c conda-forge pyimagej=1.4.1 openjdk=11 maven

use whatever installer you use but the most important part is that last command. 
Please use that version of pyimagej, otherwise you'll go through the heartbreak that I had to go through to run
pyimagej and its versions.

Then, go into view and run python main_view.py

To run tests:
run the command from the root and it should show the coverage and tests for all available files.
pytest --cov
