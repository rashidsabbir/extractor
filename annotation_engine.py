#!/usr/bin/python
'''general approach:
    construct a high-dimension space of meaning for the various attributes under consideration
    develop algorithms to map an input string to a point in this space
    Approaches may include:
        Naive text analysis, adding a vector corresponding to each word + nearest neighbor
        Neural network, possibly recurrent, though I will need training data
        transform into a more compact feature space + nearest neighbor
        encoder-decoder method borrowed from modern machine translation'''
        
# import and network attributes from labkey
# requires pip install labkey, poolmanager, pydictionary
# This script targets the client api version 0.4.0 and later

#be sure to create a .netrc file (_netrc on windows) in your "home" directory
#the contents of ~/.netrc should look like this:
#machine chear.tw.rpi.edu
#login <your email address>
#password <your password>
#also you should modify the access to .netrc to read/write exclusively for you (for security)
import labkey
from PyDictionary import PyDictionary
import utils
from sklearn.neighbors import LSHForest
from Tkinter import *
#from atk import Window
import os
import time
from tkFileDialog import askopenfilename
import tkFileDialog

#get the target file
rt = Tk()
rt.withdraw()
filepath = tkFileDialog.askopenfilename()
rt.destroy()

dict = PyDictionary()
stemAll = utils.stemAll

server_context = labkey.utils.create_server_context('chear.tw.rpi.edu', 'CHEAR Development', 'labkey')

class config:
    
    def __init__(self):
        self.columns = ['Attribute','attributeOf', 'Unit', 'Time', 'Entity', 'Role', 'Relation', 'inRelationTo', 'wasDerivedFrom', 'wasGeneratedBy', 'hasPosition']
        self.all_sources = {'Attribute' : ['Attribute', 'DASchemaAttribute'],
                            'attributeOf' : ['AgentType'],
                            'Unit' : ['Unit'],
                            'Time' : [], 
                            'Entity' : [],
                            'Role' : ['LocalRoleType'],
                            'Relation' : [], 
                            'inRelationTo' : [], 
                            'wasDerivedFrom' : [], 
                            'wasGeneratedBy' : [], 
                            'hasPosition' : []                           
                             }
        self.all_fields = {'Attribute' : ['hasURI', 'rdfs:label'],
                           'attributeOf' : ['hasURI', 'rdfs:label'], 
                           'Unit' : ['hasURI', 'rdfs:label'],
                           'Time' : ['hasURI', 'rdfs:label'], 
                           'Entity' : ['hasURI', 'rdfs:label'],
                           'Role' : ['hasURI','rdfs:label','skos:definition'], 
                           'Relation' : ['hasURI', 'rdfs:label'], 
                           'inRelationTo' : ['hasURI', 'rdfs:label'], 
                           'wasDerivedFrom' : ['hasURI', 'rdfs:label'], 
                           'wasGeneratedBy' : ['hasURI', 'foaf:name'], 
                           'hasPosition' : ['hasURI', 'rdfs:label'] 
                           }
        self.schema = 'lists'
    def getColumns(self):
        return self.columns
    def getSources(self, column):
        return self.all_sources[column]
    def getFields(self, column):
        return self.all_fields[column]
    def getSchema(self):
        return self.schema
#construct and extract
cf = config()  

#maps the set of strings from a row to a point in a high dimensional space
def rowToPoint(row, rowToPointDict):
    if(rowToPointDict.has_key(row)):
        return rowToPointDict[row]
    point = {}
    row_strs = stemAll(row)
    for word in row_strs:
        if point.has_key(word):
            point[word] += 1
        else:
            point[word] = 3
        #perhaps add a clause for part of speech as well as for words' synonyms
    rowToPointDict[row] = point
    return point

#defines the dimensions and returns number of dimensions
def getDimensions(point_dict, DimensionDict):
    index = 0
    for key in point_dict.keys():
        words = stemAll(key)
        for word in words:
            if not DimensionDict.has_key(word):
                DimensionDict[word] = index
                index += 1
    return index

def pointToArray(point, dimension, DimensionDict, rowToPointDict):
    arr = [0] * dimension
    keys = stemAll(point)
    for key in keys:
        if DimensionDict.has_key(key):
            arr[DimensionDict[key]] = rowToPointDict[point][key]
    return arr

def stringToCoordinates(str, dimension, DimensionDict):
    arr = [0] * dimension
    keys = stemAll(str)
    for key in keys:
        if DimensionDict.has_key(key):
            arr[DimensionDict[key]] = 3
    return arr

class modelRep:
    def __init__(self, sources, fields):
        self.sources = sources
        self.row_strings = []
        self.labels = {}
        self.points = {}
        self.rowToPointDict = {}
        self.DimensionDict = {}
        self.trainX = []
        self.trainY = []
        self.dimension = 1
        self.lshf = LSHForest()
        if(sources == []):
            self.sources = []
            return
        self.buildRep(sources, fields)
           
    def buildRep(self, sources, fields):  
        for source in sources:
            my_results = labkey.query.select_rows(
                server_context=server_context,
                schema_name=cf.getSchema(),
                query_name=source)
            rows = my_results['rows']
            for row in rows:
                row_str = ""
                for field in fields:
                    if row[field]: row_str = row_str + row[field].encode('utf8') + ","
                row_str = row_str[:-1]
                #print row_str
                self.row_strings.append(row_str)
                str_parts = row_str.split(',')
                if(len(str_parts) > 1):
                    label = row_str.split(',')[0] + "," + row_str.split(',')[1]
                else:
                    label = row_str.split(',')[0] #str(row['hasURI']) #+ "," + str(row['rdfs:label'])
                self.labels[row_str] = label
                rowToPoint(row_str, self.rowToPointDict)
        self.dimension = getDimensions(self.rowToPointDict, self.DimensionDict)
        for row_str in self.row_strings:
            self.points[row_str] = pointToArray(row_str, self.dimension, self.DimensionDict, self.rowToPointDict)
            self.trainX.append(self.points[row_str])
            #trainY.append(point)
            self.trainY.append(self.labels[row_str])
        self.lshf.random_state = 123
        self.lshf.fit(self.trainX)

    def getNeighbors(self, tests, n_neighbors):
        if self.sources == []:
            return [0] * n_neighbors, [1] * n_neighbors
        testX = []
        for str in tests:
            testX.append(stringToCoordinates(str, self.dimension, self.DimensionDict))
        distances, indices = self.lshf.kneighbors(testX, n_neighbors=n_neighbors)
        return distances, indices
    


#path = 'sdd_t2/Examination/BMX_H_Doc-SDD.csv'
path = filepath
dirs = path.split('/')
def enterName():
    rt.destroy()
# get the user's destination directory
rt = Tk()
userV = StringVar()
userV.set('default')
Label(rt, wraplength=600,
              text='Enter the name of your session, e.g. your name',
              justify = LEFT).pack()
userE = Entry(rt, text = 'default', textvariable = userV)
userE.pack()
Button(rt, text="Enter", command = enterName).pack()
mainloop()
user_dn = userV.get()
print user_dn

# direct session data to files, a session is specific to an input file, and uses the same dirctory structure
top_dn = "sessions"
session_fn = path
n_neighbors = 10

if not os.path.exists(top_dn):
    os.makedirs(top_dn)
if not os.path.exists(top_dn + "/" + user_dn):
    os.makedirs(top_dn + "/" + user_dn)
pathVar = top_dn + "/" + user_dn
for i in range(0, len(dirs) - 1):
    pathVar = pathVar + "/" + dirs[i]
    if not os.path.exists(pathVar):
        os.makedirs(pathVar)

session = open(top_dn + "/" + user_dn + "/" + session_fn,"w")

with open(path, 'r') as myfile:
    tests = myfile.read().split("\n")
myfile.close()
head = tests.pop(0) #remove the header line
session.write(head + "\n")

#get all the guess data for each column
models = {}
all_dists = {}
all_indices = {}
for column in cf.getColumns():
    model = modelRep(cf.getSources(column), cf.getFields(column))
    models[column] = model
    distances, indices = model.getNeighbors(tests, n_neighbors) 
    all_dists[column] = distances
    all_indices[column] = indices

base = Tk()
root = Frame(base)
root.pack()

row_index = IntVar()
col_index = IntVar()
v = IntVar()
uri = StringVar()
lab = StringVar()
label_contents = StringVar()
radio_contents = [StringVar() for i in range(n_neighbors + 3)]

row_index.set(0)
col_index.set(0)
columns = cf.getColumns()
column = ""

class SelectionWindow(object):
    def __init__(self, **kwargs):
        self.windowPosition()
        self.refreshWindow()
        
    def printChoice(self):
        print v.get()
    def enterChoice(self):  
        column = columns[col_index.get()]
        model = models[column]
        indices = all_indices[column]
        distances = all_dists[column]
        
        if col_index.get() == 0:
            st = "%s,%s,%s,%s,%s" % tuple(tests[row_index.get()].split(',')[0:5])
            print st
            session.write(st)
        if v.get() < n_neighbors and v.get() >= 0:
            sel = model.trainY[indices[row_index.get()][v.get()]]
            sel = sel.split(',')[0]
            print "selected: " + sel
            session.write("," + sel)
        if v.get() == n_neighbors:
            sel = tests[row_index.get()].split(",")[col_index.get() + 5]
            print "selected: " + sel
            session.write("," + sel)
        if v.get() == n_neighbors + 1:
            sel = "none,N/A or Unknown"
            print "selected: " + sel
            sel = sel.split(',')[0]
            session.write("," + sel)
                
        if v.get() == n_neighbors + 2:
            sel = uri.get() + "," + lab.get()
            print "selected: " + sel
            sel = sel.split(',')[0]
            session.write("," + sel)
            
        col_index.set(col_index.get()+1)
        if col_index.get() >= len(columns):
            col_index.set(0)
            row_index.set(row_index.get()+1)
            session.write("\n")
        #add selection to session data file
        #session.write(tests[row_index.get()] + "," + uri.get() + "," + lab.get() + "\n")
        for child in root.winfo_children():
            child.destroy()
        self.refreshWindow()
    
    #places window at bottom right corner
    def windowPosition(self):
        screenw = base.winfo_screenheight()
        screenh = base.winfo_screenwidth()
        winw = 600
        winh = 500
        x = screenw-winw
        y = screenh-winh
        base.geometry(('%dx%d+%d+%d' % (winw, winh, x, y)))
        
    def refreshWindow(self):
        if(row_index.get() >= len(tests)):
            base.destroy()
            return
        column = columns[col_index.get()]
        model = models[column]
        indices = all_indices[column]
        distances = all_dists[column]
        v.set(n_neighbors+1)
        uri.set("uri")
        lab.set("label")
        label_contents.set("row #"+str(row_index.get() + 1)+" of " + str(len(tests)) + ", "+ column + "\n" + 
                tests[row_index.get()])
        Label(root, wraplength=600,
              textvariable=label_contents,
              justify = LEFT,
              padx = 20).pack()
        Radiobutton(root, text="N/A or Unknown", variable=v, command = self.printChoice, value = n_neighbors+1).pack(anchor=W)
        for i in range(0, min(n_neighbors, len(model.trainY))):
            #ul = str(my_results['rows']['hasURI'][indices[row_index.get()][i]]) + "," + str(my_results['rows']['rdfs:label'][indices[row_index.get()][i]])
            radio_contents[i].set(model.trainY[indices[row_index.get()][i]] + " " + str(1-distances[row_index.get()][i]))
            Radiobutton(root, 
                        textvariable=radio_contents[i],
                        padx = 20, 
                        variable=v, 
                        command = self.printChoice,
                        value=i).pack(anchor=W)
        #uri = StringVar()
        #lab = StringVar()
        #give the current entry as an option
        if tests[row_index.get()].split(",")[col_index.get() + 5] != "":
            current = tests[row_index.get()].split(",")[col_index.get() + 5]
            radio_contents[n_neighbors].set(current)
            Radiobutton(root, 
                        textvariable=radio_contents[n_neighbors],
                        padx = 20, 
                        variable=v, 
                        command = self.printChoice,
                        value=n_neighbors).pack(anchor=W)           
        Radiobutton(root, text="Other", variable=v, value = n_neighbors + 2).pack(anchor=W)
        uriE = Entry(root, text = "URI", textvariable = uri)
        labE = Entry(root, text = "Label", textvariable = lab)
        uriE.pack(anchor=W)
        labE.pack(anchor=W)
        Button(root, text="Enter", command = self.enterChoice).pack(anchor=W)


print "path: " + path

win = SelectionWindow()
base.mainloop()

session.close()

'''
for row_index in range(len(testX)):
    v = IntVar()
    Label(root, 
          text="selection #"+str(row_index + 1)+" of " + str(len(testX)) + "\n" + 
            tests[row_index],
          justify = LEFT,
          padx = 20).pack()
    for i in range(0, n_neighbors):
        Radiobutton(root, 
                    text=trainY[indices[row_index][i]],
                    padx = 20, 
                    variable=v, 
                    command = printChoice,
                    value=i).pack(anchor=W)
    uri = StringVar()
    lab = StringVar()
    Radiobutton(root, text="Other", variable=v, value = n_neighbors).pack(anchor=W)
    uriE = Entry(root, text = "URI", textvariable = uri)
    labE = Entry(root, text = "Label", textvariable = lab)
    uriE.pack(anchor=W)
    labE.pack(anchor=W)
    
    Button(root, text="Enter", command = enterChoice).pack(anchor=W)
    mainloop()'''
    
'''
print indices
print "text = " + tests[0]
print "attribute guesses:"
for i in indices[0]:
    print trainY[i]


    row_strs = stemAll(str(row['rdfs:label']))
    print str(row['hasURI']) + ", " + str(row['rdfs:label'])
    #print row
    for word in row_strs:
        print word
        print dict.synonym(word)
    rowToPoint(row_strs)
print "SCHEMA:"
for i in my_results:
    print i
 '''   

