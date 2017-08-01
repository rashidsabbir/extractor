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
from atk import Window
import os
import time

dict = PyDictionary()
stemAll = utils.stemAll

server_context = labkey.utils.create_server_context('chear.tw.rpi.edu', 'CHEAR Development', 'labkey')

my_results = labkey.query.select_rows(
    server_context=server_context,
    schema_name='lists',
    query_name='LocalRoleType'
)

#maps the set of strings from a row to a point in a high dimensional space
rowToPointDict = {}
def rowToPoint(row):
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

DimensionDict = {}
#defines the dimensions and returns number of dimensions
def getDimensions(point_dict):
    index = 0
    for key in point_dict.keys():
        words = stemAll(key)
        for word in words:
            if not DimensionDict.has_key(word):
                DimensionDict[word] = index
                index += 1
    return index

def pointToArray(point, dimension, DimensionDict):
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

#add rows and points to the rowToPoint dictionary
points = {}
labels = {}

for row in my_results['rows']:
    row_str = str(row['hasURI']) + "," + str(row['rdfs:label']) + "," + row['skos:definition'].encode('utf8')
    #row_strs = stemAll(row_str)
    print str(row_str)
    #print row['skos:definition']
    rowToPoint(row_str)
    points[str(row_str)] = None
    labels[str(row_str)] = str(row['hasURI']) + "," + str(row['rdfs:label'])
    
    
dimension = getDimensions(rowToPointDict)

trainX = []
trainY = []

for point in points.keys():
    points[point] =  pointToArray(point, dimension, DimensionDict)
    trainX.append(points[point])
    #trainY.append(point)
    trainY.append(labels[point])
    
# build the LSH forest    
lshf = LSHForest()
lshf.fit(trainX)
# direct session data to a files, a session is specific to an input file
top_dn = "sessions_test"
user_dn = "user"
session_fn = "test_session.csv"

if not os.path.exists(top_dn):
    os.makedirs(top_dn)
if not os.path.exists(top_dn + "/" + user_dn):
    os.makedirs(top_dn + "/" + user_dn)

session = open(top_dn + "/" + user_dn + "/" + session_fn,"w")

#some test strings
#tests = ["this is the first test", "this is the second test"]

testX = []
with open('sdd_t2/Limited_Access/FSQ_H_R_Doc-SDD.csv', 'r') as myfile:
    f_test = myfile.read().split("\n")
myfile.close()

tests = f_test
for test in tests:
    testX.append(stringToCoordinates(test, dimension, DimensionDict))
    
n_neighbors = 10
distances, indices = lshf.kneighbors(testX, n_neighbors=n_neighbors)

base = Tk()
root = Frame(base)
root.pack()

x_index = IntVar()
v = IntVar()
uri = StringVar()
lab = StringVar()
label_contents = StringVar()
radio_contents = [StringVar() for i in range(n_neighbors)]

x_index.set(0)

class SelectionWindow(object):
    def __init__(self, **kwargs):
        self.windowPosition()
        self.refreshWindow()
        
    def printChoice(self):
        print v.get()
    def enterChoice(self):  
        if v.get() < n_neighbors and v.get() >= 0:
            sel = trainY[indices[x_index.get()][v.get()]]
            print "selected: " + sel
            session.write(tests[x_index.get()] + "," + sel + "\n")
            
        if v.get() == n_neighbors:
            sel = "none,N/A or Unknown"
            print "selected: " + sel
            session.write(tests[x_index.get()] + "," + sel + "\n")
                
        if v.get() > n_neighbors:
            print "selected: " + uri.get() + ", " + lab.get()
            session.write(tests[x_index.get()] + "," + uri.get() + "," + lab.get() + "\n")
        x_index.set(x_index.get()+1)
        #add selection to session data file
        #session.write(tests[x_index.get()] + "," + uri.get() + "," + lab.get() + "\n")
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
        if(x_index.get() >= len(testX)):
            base.destroy()
            return
        
        label_contents.set("selection #"+str(x_index.get() + 1)+" of " + str(len(testX)) + "\n" + 
                tests[x_index.get()])
        Label(root, wraplength=600,
              textvariable=label_contents,
              justify = LEFT,
              padx = 20).pack()
        Radiobutton(root, text="N/A or Unknown", variable=v, command = self.printChoice, value = n_neighbors).pack(anchor=W)
        for i in range(0, n_neighbors):
            #ul = str(my_results['rows']['hasURI'][indices[x_index.get()][i]]) + "," + str(my_results['rows']['rdfs:label'][indices[x_index.get()][i]])
            radio_contents[i].set(trainY[indices[x_index.get()][i]])
            Radiobutton(root, 
                        textvariable=radio_contents[i],
                        padx = 20, 
                        variable=v, 
                        command = self.printChoice,
                        value=i).pack(anchor=W)
        #uri = StringVar()
        #lab = StringVar()
        Radiobutton(root, text="Other", variable=v, value = n_neighbors + 1).pack(anchor=W)
        uriE = Entry(root, text = "URI", textvariable = uri)
        labE = Entry(root, text = "Label", textvariable = lab)
        uriE.pack(anchor=W)
        labE.pack(anchor=W)
        Button(root, text="Enter", command = self.enterChoice).pack(anchor=W)



win = SelectionWindow()
base.mainloop()

session.close()

'''
for x_index in range(len(testX)):
    v = IntVar()
    Label(root, 
          text="selection #"+str(x_index + 1)+" of " + str(len(testX)) + "\n" + 
            tests[x_index],
          justify = LEFT,
          padx = 20).pack()
    for i in range(0, n_neighbors):
        Radiobutton(root, 
                    text=trainY[indices[x_index][i]],
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

