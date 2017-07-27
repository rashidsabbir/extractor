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
import labkey
from PyDictionary import PyDictionary
import utils
from sklearn.neighbors import LSHForest

dict = PyDictionary()
stemAll = utils.stemAll

server_context = labkey.utils.create_server_context('chear.tw.rpi.edu', 'CHEAR Development', 'labkey')

my_results = labkey.query.select_rows(
    server_context=server_context,
    schema_name='lists',
    query_name='Attribute'
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

for row in my_results['rows']:
    row_strs = stemAll(str(row['rdfs:label']))
    print str(row['hasURI']) + ", " + str(row['rdfs:label'])
    rowToPoint(str(row['rdfs:label']))
    points[str(row['rdfs:label'])] = None
    
dimension = getDimensions(rowToPointDict)

trainX = []
trainY = []

for point in points.keys():
    points[point] =  pointToArray(point, dimension, DimensionDict)
    #print points[point]
    trainX.append(points[point])
    trainY.append(point)
   
test = "date of decreased dentist department drug test"
testX = stringToCoordinates(test, dimension, DimensionDict)
    
lshf = LSHForest()
lshf.fit(trainX)

distances, indices = lshf.kneighbors(testX, n_neighbors=5)

print distances
print indices
for i in indices[0]:
    print trainY[i]

'''
for row in my_results['rows']:
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

