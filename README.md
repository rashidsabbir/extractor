# README
 
### *A breakdown of everything in the extractor repository*

## Installation
Currently, installation has only been tested in Ubuntu versions 14.04 and 16.04.

### Instructions

run the following commands in your terminal
> sudo apt-get install python-pip python-dev build-essential python-tk

> sudo pip install --upgrade pip 

> sudo pip install --upgrade virtualenv

now you can either install scripts from source code, or directly through pip.

#### From source:
Install git, from the terminal:
> sudo apt-get install git

Change to your desired installation directory in the terminal, and then run
> git clone https://github.com/rashidsabbir/extractor.git

Change directory to extractor
> cd extractor

And install
> sudo -H pip install -e .

Now the NHANES\_extractor\_exp.py and annotation\_engine.py scripts are ready to run from the terminal.


## NHANES Extractor
The files "NHANES\_extractor.py" and "NHANES\_extractor\_exp.py" automatically extract semantic data dictionaries, codebooks, and acq files from web-based sources.  The automatically extracted SDDs are incomplete and the entries given may not always be correct however, so human annotation is still necessary.  For information about how to annotate SDD files, please see "annotation\_instructions.md".

The "NHANES\_extractor\_exp.py" script is more advanced and accurate, so in general you should run it in favor of "NHANES\_extractor.py".  The structure of the latter script is simpler, so if you are looking to extend these programs, it is a good resource to get the gist of how they work.

## Annotation Engine
The file "annotation\_engine.py" is a script designed to streamline the annotation process with a graphical user interface.  It extracts information about relevant ontologies from online sources and computes a number of guesses as to the appropriate annotations for any given line in an input SDD file.

To use the annotation engine, you must have access priveleges on the CHEAR labkey server, and create a .netrc file (_netrc on windows) in your "home" directory
the contents of ~/.netrc should look like this:
> machine chear.tw.rpi.edu

> login <your email address>

> password <your password>

also you should modify the permissions to .netrc to read/write exclusively for you (for security)

When the engine runs, a GUI will pop up with the first line of the given SDD along with some information, and a set of radio buttons with different options are presented.  The column header of the SDD you are annotating will appear at the top, and the row below it.  The radio buttons include 3 types:
The top produces a placeholder N/A, the indented middle buttons list a number of guesses and an estimate of their confidence, and the bottom button allows other input that is not specified by the other buttons.  If you wish to input an annotation not shown, type the URI in the top text box, and optionally a label for the URI in the bottom box.  On pressing "Enter", your selection will be output to a csv file under the "sessions" directory.




This python code uses the Beautiful Soup package to extract codebook values and Semantic Data Dictionary (SDD) starting points from NHANES documents.

To specify which year's variables to extract from, set the starting year on the begin_year variable. As 2013-2014 data is the most up to date and complete at the time of this writing, begin_year has been set to 2013.

The *Val variables are used to store the SDD column values.

columnVal stores the name of the NHANES variable, which is required.
labelVal stores the label associated with the NHANES variable, extracted from "SAS Label"
commentVal stores the comment associated with the NHANES variable, extracted from "English Text"
noteVal stores a note associated with the NHANES variable, extracted from "English Instructions"
targetVal stores the target of the variable, extracted from "Target" . This column is not in the SDD specification, but is included in the extraction for completeness.
attributeVal stores the attribute associated with the variable, using text matching.
attributeOfVal is used to assign a role.
unitVal is used to assign a unit to the variable as extracted from the label or comment.

The following variable are placeholders for future code that can be written to assign values to their associated columns.
timeVal
entityVal 
roleVal
relationVal
inRelationToVal
wasDerivedFromVal
wasGeneratedByVal
hasPositionVal
