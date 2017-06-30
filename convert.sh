#!/bin/bash
#moves .ods files from sdd annotated to annotated csv and converts them there to .csv files
rsync -av --exclude=*.csv sdd\ annotated/ annotated\ csv
find annotated\ csv -name '*.ods' -execdir libreoffice "-env:UserInstallation=file:///tmp/LibO_Conversion" --headless --invisible --convert-to csv {} \;
find annotated\ csv -name '*.ods' -delete