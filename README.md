# AxonLabPipeline

To Downlaod For Windows verson:
>Windows: pipeline.exe

Open the **Actions** tab in GitHub  
- Select **Build Windows EXE** from the workflow list  
- Click the most recent successful build (usually the top entry)  
- Scroll down to the **Artifacts** section  
- Download the **Pipeline-Windows-EXE** artifact <br><br>

To Download For Mac verson:
>Mac: pipeline.dmg

* Click on the file in the repository and download the raw file.

<h5> Run the application how you would any desktop app. </h5><br>

*************************************

<h1> Manual Mode </h1>
<h4> Run these command in the terminal if the desctop app does not work. </h4> 

1. <h4>Install Conda.</h4>
Go to https://www.anaconda.com/download/success and download the 64-bit installer for your operating system. 

Going through the installation process on the last step, make sure to check the box that says "**Add Anaconda to my PATH environment variable**". This will allow you to run conda commands from the terminal. <br>
* Note: i would also recomment keeping the create shortcut, if registering Anaconda does not work. You can open the Anaconda Prompt and run the command `conda init` and close out and it should work in any terminal.

To verify that Conda is installed correctly, open a terminal and run the command `conda --version`. If it returns the version number, then Conda is installed correctly. <br><br>

2. <h4>Create a Conda Virtual Environment and install the dependencies.</h4>

```
conda create -n lexisenvironment -c conda-forge python=3.10 pyimagej openjdk=11 maven opencv numpy scipy pandas pytest pytest-cov
```
* Note: the name of the Conda Virutal Environment (`lexisenvironment`) can be whatever you want, just make sure to remember it for the next step<br><br>


3. <h4>Activate the Conda Virtual Environment</h4>
```
conda activate lexisenvironment
```
* Note: if you want to exit the Conda Virutal Environment, just run the command `conda deactivate`<br>
4. <h4>Install Pyimage</h4>
```
conda install -c conda-forge pyimagej=1.4.1 openjdk=11 maven
```

use whatever installer you use but the most important part is that last command. 
Please use that version of pyimagej, otherwise you'll go through the heartbreak that I had to go through to run
pyimagej and its versions.

5. <h4>Run Main_view.py</h4>

Then, go into the view folder by typing `cd view` and run `python main_view.py`

<h3> Running Tests in the Terminal </h3>

run the command `pytest --cov` from the root and it should show the coverage and tests for all available files. 
