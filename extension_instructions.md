# Extending the extractor scripts

## How to update the pip installation proceedure

Currently, the package on pypi is registered to Ryan Sherman, and co-owned by Sabbir Rashid.  If you would like to update the pypi package you may need to contact one of them for permission.  Alternatively, you can change the "name" argument in setup.py to create a different package under your own ownership.

A full tutorial for uploading to pypi is available here, look through it first for information on registering an account and creating a .pypirc file:

https://packaging.python.org/tutorials/distributing-packages/

After initial setup, the normal proceedure is as follows:
1) Make your changes to source files
2) Update setup.py:
	-make sure to add any newly required pip-installable dependencies to the install_requires argument to setup
	
	-Iterate the version number in setup.py
	
	-If you want to add any new scripts, add them to the scripts argument to setup
	
3) Build the new distribution
	> sudo python setup.py sdist
4) Upload with twine
	> twine upload dist/\<new dist name\>

	

Remember to iterate the version number in setup.py whenever you upload changes

## Suggested new functionality

There are a number of features that may be added to these scripts to extend their functionality.  At the moment, the alpha build available offers useful, but incomplete functionality.

Here is a list of features we have considered but not yet implemented.

### NHANES extractor full digest
The NHANES extractor script currently runs only on the 2013-14 data set.  Extending this script to run on all the NHANES years should be very simple, although the already somewhat long runtime would be multiplied.  As such, I would recommend that this extension be made as either a command line option or as another script.

### More annotation engine sources
The config class in the annotation engine has several tables from labkey from which is draws recommended entries.  Some columns do not have sources listed.  Adding tables or table names containing relevant entries is a straightforward improvement to be made.

Additionally, other databases could be accessed for the same types of data, although this will take some degree of refactoring.

### Improved annotation recommendations
The current model for recommending annotations is fairly simple:
Strings corresponding to each database entry are placed in a high-dimensional space based on word frequencies.  These points are placed in an LSH Forest (this is essentially a fast approximate nearest-neighbors implementation for high dimensions).  Then, strings from each row in an SDD placed in the same space, and a number of nearest neighbors are found along with their cosine distances.

Some details about possible improvements via machine learning are listed at the top of the recommendation\_engine.py file.






