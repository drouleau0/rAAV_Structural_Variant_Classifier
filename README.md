# Repository for *"Structural Analysis of Recombinant AAV Vector Genomes at Single-Molecule Resolution"*  
>last tested on python version 3.14.2
---
  
Included is vector subparser program and data used as described in the research article at ____.  
The purpose of the program is to take AAV sequences from a long-read sequencing run and categorize them into structural variants.  
   
Its required inputs are:  
1. The desired rAAV payload size  
2. A counts file output from the tiling algorithm (https://github.com/bruc/tiling)  
3. The directory to store output files  
Its outputs are:  
1. A tsv containing structural variant classification data such as counts and proportions of each structural variant  
2. A pdf with a bar chart and pie plot summarizing structural variant data   
3. A folder with counts files containing sequences for each structural variant separated into different files to facilitate further analysis of structural variant sequences   
  
Optional arguments for the program are described further by using the -h option in the command line.  
example: "python3 parse_file.py -h"  
Additionally, jupyter notebooks used to generate the data in the manuscript are included in the **/DataFiles/Outputs/** directory.  

The **CodeFiles** directory contains the subparser python scripts and the test file used for doing unit testing.   
The parse_file.py program is run in the command line, and the tile_classes.py and parse_file.py scripts are modules used by parse_file.py.  
The **DataFiles** directory contains data used for integration testing as well as input and output data described in the manuscript.    
 
---

Also included is the sequence generator program used to generate the *in silico* data used in the manuscript, stored in the **Sequence Generator** Directory.  
In this directory is the code files, input files, and bash script used for running the code files that was used to generate the *in silico* sequences.  
The test code for the sequence generator is also included.
To run the sequence generator to recreate the in silico data used in the manuscript:
1. Ensure the requirments in requirements.txt are installed
2. Run the file run_generator.sh in the SequenceGenerator directory

The output will be at the following directory: /DataFiles/Inputs/InSilicoData/raw/

---

**Quick Start Guide:**
1. Download the repo either through `git clone` or through downloading the zip file in the web browser and extracting it in your file browser
2. Create a python virtual environment with `python -m venv venv`
3. Activate the virtual environment with `source venv/Scripts/activate`
4. Download dependencies to the virtual environment with `pip install -r requirements.txt`
5. You can now run the program with the command line. To quickly see it in use, run the included quick_start.sh file with `./quick_start.sh`
