# AxonLabPipeline

things about running:
at this point, to run the analysis stuff you need to make a virtual environment with the necessary libraries;

conda create -n <NAME OF ENVIRONMENT HERE> -c conda-forge python=3.10 pyimagej openjdk=11 maven
conda activate <NAME OF ENVIRONMENT HERE>

conda install -c conda-forge pyimagej=1.4.1 openjdk=11 maven

use whatever installer you use but the most important part is that last command. 
Please use that version of pyimagej, otherwise you'll go through the heartbreak that I had to go through to run
pyimagej and its versions.

To run Ezra's stuff, you need to install these libraries in the virtual environment. You don't need to make a new virtual environment for it, just make sure on the existing environment you made using the instructions above, you need these:

pip install opencv-python
pip install numpy
pip install tifffile
pip install scipy
pip install pandas

Also I realized I didn't include necessary stuff to run testing:
pip install pytest
pip install pytest-cov

run the command from the root and it should show the coverage and tests for all available files.
pytest --cov