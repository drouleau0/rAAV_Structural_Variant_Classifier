# Repository for *"Structural Analysis of Recombinant AAV Vector Genomes at Single-Molecule Resolution"*   
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
The test code is also included.

---
# Extending the program for noncannonical rAAV structural variant calling

The manuscript for this program is primarily concerned with structural variant calling of cannonical rAAV genomes, which are rAAV genomes without contaminant DNA.
All genomes which are determined to contain sequences that aren't within the reference AAV genome were filtered out to focus on these canonical genomes.
Since it may be desirable by others to use this program to classify noncannonical genomes, such as those with DNA from helper plasmids used in rAAV production, it has been written such that it can be extended to do so.

There are many ways one might modify the program to do classify noncannonical genomes, but the way I found easiest was by means of a additional lexing function. With a lexing function, one can tokenize an entire tile pattern based on simple logic regarding the context a single tile. By doing this, you do not need to modify the current rules of the parser's CFG, and don't need to worry about rule ambiguity or combinatorial explosion of grammar rules. An example of doing this to classify RepCap-containing sequences into four separate classifications has already been added to vector_subparser.py module for reference along with comments.
The following steps detail how to do this:
1. Use the -n flag when running parse_file.py on the command line to disable filtering out of noncannonical genomes. With this flag raised, any tile pattern with a tile unknown to the vector_subparser module is classified as "other". Without it, tile patterns with noncanonical sequence are removed from analysis completely.
2. Modify the vector_subparser module's VectorLexer class to tokenize tile patterns based on the context of the tile of interest: (in the example it is RepCap) 
    1. Add one new token to the lexer class for each desired new variant classification to detect (see line 25 in vector_subparser.py)
    2. Add the lexing function for tokenizing noncannonical variants into the tokens added in step 2.1 based on desired logic (see line 50 in vector_subparser.py) IMPORTANT: It is necessary to put such functions above the canonical related lexing functions to override them
3. Modify the vector_subparser module's VectorSubParser class to classify the tokens that the modified VectorLexer is now generating: (comments and code for this have been added as well)
    1. (optional) new parsing rules can be added for more complex structural variants if desired. The example given in code using a lexing function shows that this should not be necessary if only the context of a noncanonical tile is of importance, but the -debug flag of the program and the __main__ function of the vector_subparser.py file can be used to give extensive debugging information to any user who wishes to delve into modifying the program’s CFG. It is recommended that such a user familiarizes themselves well with the PLY documentation.
    2. Add the new tokens from step 2 to the end state rule of the parser. (see lines 162-166 in vector_subparser.py)
