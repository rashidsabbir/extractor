# Annotation

Annotating semantic data dictionaries (SDDs) is the process of assigning ontological values to different attributes in every row of an SDD, as well as identifying additional entites that should be defined on their own row.  The packages contained here aid in the first part of this task.

The NHANES extractor script (exp version) will generate helpful starting points, containing all the rows that are explicitly in each NHANES study.  This script runs some analysis itself, and generates entries for some of the cells in the SDD.  The annotation engine script is built to help you fill in the rest.  The specifics of how to use the programs are in the README.md file (on our github home page https://github.com/rashidsabbir/extractor)

This document instead contains information to help with annotating.

## Resources

There are several online resources that can help you find the right annotation.

http://www.ontobee.org/ lets you search a large collection of ontologies

https://chear.tw.rpi.edu/labkey/ contains many useful ontology entries, if you have access.  Tables from this site are used in the annotation engine.

https://ibm.ent.box.com/notes/178179782606?s=2yd000wdkfs6sig2zy9us3sog9rc7jnr lists the HEALS supporting ontologies with helpful links

## Tips

You should prefer to use URIs (the codes associated with ontology entries) from SIO, and from the CHEAR ontology, and then from the HEALS supporting onologies.

Some cells in an SDD may not need to be filled

Looking at examples can be very helpful, ask Sabbir Rashid for well-annotated examples

The code here is open source under MIT license, and so you are more than welcome to make your own modifications to the source code to suit your needs.  Some suggested upgrades are detailed in extension\_instructions.md.  If you would like to merge a useful change into the code, we'll be happy to help.






