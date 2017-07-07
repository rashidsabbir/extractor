from bs4 import BeautifulSoup
from stemming.lovins import stem

import urllib
import requests
import os
import re
import csv
import urllib2
import inflect
import operator

codebook_dn = "codebook_t2"
sdd_dn = "sdd_t2"

if not os.path.exists(codebook_dn):
    os.makedirs(codebook_dn)
if not os.path.exists(sdd_dn):
    os.makedirs(sdd_dn)


code_mappings_url = 'https://raw.githubusercontent.com/tetherless-world/chear-ontology/master/code_mappings.csv'
code_mappings_response = urllib2.urlopen(code_mappings_url)
code_mappings_reader = csv.reader(code_mappings_response)

unit_code_list = []
unit_uri_list = []
unit_label_list = []

for code_row in code_mappings_reader :
    unit_code_list.append(code_row[0])
    unit_uri_list.append(code_row[1])
    unit_label_list.append(code_row[2])
del unit_code_list[0]
del unit_uri_list[0] 
del unit_label_list[0]   
#r2013 = urllib.urlopen('https://wwwn.cdc.gov/Nchs/Nhanes/continousnhanes/default.aspx?BeginYear=2013')
begin_year = 2013
r = requests.get("https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=" + begin_year.__str__())
data = r.text

soup = BeautifulSoup(data, "lxml")
list_items = soup.find("h3",text="Data, Documentation, Codebooks, SAS Code").findNext("ul").findAll("li")

#return the tokenized list of words and punctuation in a string, save seen entries to dict for speed
tokenDict = {}
def tokens(str):
    if(tokenDict.has_key(str)):
        return tokenDict.get(str)
    toks = re.findall(r"[\w]+|[.,!?;^()'/%*]", str)
    tokenDict[str] = toks
    return toks
stemmed = {}
#singularizes words, this version is good for units
inf = inflect.engine()
exclusions = []
exclusions.extend(("s", "S", "a", "A", "i", "I", "", "ME"))
def stemAll(str):
    if(stemmed.has_key(str)):
        return stemmed.get(str)
    toks = tokens(str)
    stems = []
    for tok in toks:
        single = inf.singular_noun(tok)
        if(single != False) and not (single in exclusions): #and (not (single in exclusions)) and (tok.lower() != "s"):
            stems.append(single)
        else:
            #if not (tok in exclusions):
            stems.append(tok)
            #else: stems.append("second")
                
    stemmed[str] = stems
    return stems
#check whether a list contains another list as a subsequence
def contains(small, big):
    for i in xrange(len(big)-len(small)+1):
        for j in xrange(len(small)):
            if big[i+j] != small[j]:
                break
        else:
            return True
    return False
#take an entry string
#attempt to return a known unit's uri, nothing or a useful filler if it fails
def unitMapper(labelVal, commentVal, noteVal, unit_label_list, unit_code_list):
    # approach: stem+tokenize, gather supporting evidence for each unit_label
    # return unit_uri with max evidence
    evidence = {}
    for unit_label in unit_label_list :
        stemUnit = stemAll(unit_label.lower())
        stemVal = stemAll(labelVal.lower() + " " + commentVal.lower() + " " + noteVal.lower())
        if contains(stemUnit, stemVal) and len(stemUnit) > 0 :
            unit_index = unit_label_list.index(unit_label)
            unit_uri = unit_uri_list[unit_index]
            evidence[unit_uri] = 1
            if(contains(["in"] + stemUnit, stemVal)):
                evidence[unit_uri] += 2
            if(contains(["("] + stemUnit + [")"], stemVal)):
                evidence[unit_uri] += 3
    for unit_code in unit_code_list :
        if len(unit_code) < 2 :
            continue
        stemVal = stemAll(labelVal + " " + commentVal + " " + noteVal)
        stemUnit = stemAll(unit_code)
        if contains(stemUnit, stemVal) and len(stemUnit) > 0 :
            unit_index = unit_code_list.index(unit_code)
            unit_uri = unit_uri_list[unit_index]
            if(evidence.has_key(unit_uri)):
                evidence[unit_uri] += 1
            else:
                evidence[unit_uri] = 1
            if(contains(["in"] + stemUnit, stemVal)):
                evidence[unit_uri] += 2
            if(contains(["("] + stemUnit + [")"], stemVal)):
                evidence[unit_uri] += 3
    constructs = unitConstructor(labelVal+" "+commentVal+" "+noteVal, unit_code_list, unit_label_list)
    for construct in constructs:
        if(construct in unit_code_list):
            unit_index = unit_code_list.index(construct)
            unit_uri = unit_uri_list[unit_index]
            if(evidence.has_key(unit_uri)):
                evidence[unit_uri] += 3
            else:
                evidence[unit_uri] = 3
    try:
        best_match = max(evidence.iteritems(), key=operator.itemgetter(1))[0]
        #print unit_code_list[best_match] + " " + unit_label_list[best_match]
        bm_index = unit_uri_list.index(best_match)
        '''if(unit_code_list[bm_index] in ["ME", "As"]): #useful bit of code for debugging
            print unit_code_list[bm_index] + " " + unit_label_list[bm_index] + " " + evidence[best_match] + "\n"
            print stemAll(labelVal + " " + commentVal + " " + noteVal + "\n\n")
            print (labelVal + " " + commentVal + " " + noteVal)'''
        return best_match
    except:
        return (-1)
    
#constructs composite unit codes from strings for direct identification or to give hints   
def unitConstructor(str, unit_code_list, unit_label_list):
    toks = tokens(str)
    words = []
    for tok in toks:
        single = inf.singular_noun(tok)
        if(single != False):
            words.append(single)
        else:
            words.append(tok)
    constructs = []
    constructs.append("")
    count = 0
    iter = 0
    stored = "none"
    for word in words:
        if word in unit_code_list or word in unit_label_list or word in ["per", "/", ".", "*", "times", "squared", "cubed", "square", "cubic", "-"]:
            if word == "per":
                constructs[iter] += "/"
            if word == "*" or word == "times":
                constructs[iter] += "."
            if(word == "squared"):
                constructs[iter] += "2"
            if(word == "cubed"):
                constructs[iter] += "3"
            if not word in ["per", "*", "times", "squared", "cubed", "square", "cubic"]:
                if(word in unit_label_list):
                    index = unit_label_list.index(word)
                    constructs[iter] += unit_code_list[index]
                else:
                    constructs[iter] += word
            if(stored != "none"):
                constructs[iter] += stored
                stored = "none"
            if(word == "square"):
                stored = "2"
            if(word == "cubic"):
                stored = "3"
            count += 1
        else:
            if(stored != "none"):
                constructs[iter] += stored
                stored = "none"
            if count >= 2:
                count = 0
                iter += 1
                constructs.append("")
            else:
                count = 0    
                constructs[iter] = ""
                
    return constructs   

for item in list_items :
    link = "https://wwwn.cdc.gov" + item.findNext("a").get("href")
    print "\tPortal: " + link
    portal_soup = BeautifulSoup(requests.get(link).text, "lxml")
    variable_link = "https://wwwn.cdc.gov/nchs/nhanes/search/" + portal_soup.find("span",id="lblVarlist").findNext("a").get("href")
    print "\tVariable List: " + variable_link
    #variable_soup = BeautifulSoup(requests.get(variable_link).text, "lxml")
    subfolder_name = item.findNext("a").contents[0].replace(" ","_")
    if not os.path.exists(codebook_dn + "/" + subfolder_name) :
        os.makedirs(codebook_dn + "/" + subfolder_name)
    if not os.path.exists(sdd_dn + "/" + subfolder_name) :
        os.makedirs(sdd_dn + "/" + subfolder_name)
    doc_rows = portal_soup.find("table",id="GridView1").find("tbody").findAll("tr")
    for row in doc_rows:
        if not (row.find("a").get("href") is "#"):                            
            doc_link = "https://wwwn.cdc.gov" + row.find("a").get("href")
            print "\tDocument: " + doc_link
            doc_soup = BeautifulSoup(requests.get(doc_link).text, "lxml")
            try:
                sdd_fn="_".join(row.find("a").contents[0].split())+ "-SDD.csv"
                print "\t\tWriting to "+ sdd_dn + "/" + subfolder_name + "/" + sdd_fn
                sdd = open(sdd_dn + "/" + subfolder_name + "/" + sdd_fn,"w")
                sdd.write("Column,Label,Comment,Note,Target,Attribute,attributeOf,Unit,Time,Entity,Role,Relation,inRelationTo,wasDerivedFrom,wasGeneratedBy,hasPosition\n")
                codebook_fn="_".join(row.find("a").contents[0].split())+ "-CB.csv"
                print "\t\tWriting to " + codebook_dn + "/" + subfolder_name + "/" + codebook_fn          
                codebook = open(codebook_dn + "/" + subfolder_name + "/" + codebook_fn,"w")
                codebook.write("Column,Variable,Label\n")
                entries=doc_soup.find("div", id="Codebook").findAll("div")
                for entry in entries :
                    #try:
                    #    print "\t\t" + entry.find("dl").find("dt",text="Variable Name: ").findNext("dd").contents[0] + " - " + entry.find("dl").find("dt",text="English Text: ").findNext("dd").contents[0]
                    #except:
                    #    try:
                    #        print "\t\t" + entry.find("dl").find("dt",text="Variable Name: ").findNext("dd").contents[0] + " - " + entry.find("dl").find("dt",text="SAS Label: ").findNext("dd").contents[0]
                    #    except:
                    #        print "\t\t" + entry.find("dl").find("dt",text="Variable Name: ").findNext("dd").contents[0]
                    
                    # Insert Semantic Data Dictionary Entries
                    
                    columnVal = entry.find("dl").find("dt",text="Variable Name: ").findNext("dd").contents[0].replace("\t","").replace("\n","").replace("\r","")
                    labelVal = ""
                    commentVal = ""
                    noteVal = ""
                    targetVal = ""
                    attributeVal = ""
                    attributeOfVal = ""
                    unitVal = ""
                    timeVal = ""
                    entityVal = ""
                    roleVal=""
                    relationVal = ""
                    inRelationToVal = ""
                    wasDerivedFromVal = ""
                    wasGeneratedByVal = ""
                    hasPositionVal = ""
                    
                    try :
                        labelVal = '"' + entry.find("dl").find("dt",text="SAS Label: ").findNext("dd").contents[0].encode('ascii','ignore').decode('utf-8').replace("\"","'") + '"'
                    except :
                        # Don't update labelVal
                        pass
                        #labelVal = ""
                    try :
                        commentVal = '"' + entry.find("dl").find("dt",text="English Text: ").findNext("dd").contents[0].encode('ascii','ignore').decode('utf-8').replace("\"","'").replace("\t","").replace("\n","").replace("\r","") + '"'
                    except :
                        # Don't update commentVal
                        pass
                        #commentVal = ""
                    try :
                        noteVal = '"' + entry.find("dl").find("dt",text="English Instructions: ").findNext("dd").contents[0].encode('ascii','ignore').decode('utf-8').replace("\"","'").replace("\t","").replace("\n","").replace("\r","") + '"'
                    except :
                        # Don't update noteVal
                        pass
                        #noteVal = ""
                    try :
                        targetVal = '"' + entry.find("dl").find("dt",text="Target: ").findNext("dd").contents[0].replace("\t","").replace("\n","").replace("\r"," ") + '"'
                    except :
                        # Don't update targetVal
                        pass
                        #targetVal = ""
                    try :
                        #if(("age" in labelVal.lower()) or ("age" in commentVal.lower()) or ("age" in noteVal.lower())) :
                        if("age" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:Age"
                        if("weight" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="chear:Weight"
                        if("height" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:Height"
                        if("race" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:Race"
                        if("ethnic" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:Ethnicity"
                        if("circumference" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:Circumference"
                        if("status" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:StatusDescriptor"
                        if("education" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="chear:EducationLevel"
                        if("language" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="chear:Language"
                        if("income" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="chear:Income"
                        if("country" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:Country"
                        if(("#" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("number of" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            attributeVal="sio:Quantity"
                        if("ratio" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:Ratio"
                        if("time" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeVal="sio:TimeInterval"
                    except :
                        # Don't update attributeVal
                        pass
                        #attributeVal = ""
                    try :
                        if("child" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeOfVal = "??child"
                        if("mother" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeOfVal = "??mother"
                        if("father" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            attributeOfVal = "??father"
                    except :
                        # Don't update attributeOfVal
                        pass
                        #attributeOfVal = ""
                    try :                                
                        if (("gram" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(g)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000021"
                        if (("milligram" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(mg)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000022"
                        if (("microgram" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(ug)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000023"
                        if (("meter" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(m)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000008"
                        if (("kilogram" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(kg)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000009"
                        if(("second" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))or ("(s)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000010"
                        if (("centimeter" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(cm)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000015"
                        if (("millimeter" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(mm)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000016"
                        if(("millisecond" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(ms)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000028"
                        if(("microsecond" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(us)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000029"
                        if(("picosecond" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) or ("(ps)" in (labelVal.lower() or commentVal.lower() or noteVal.lower()))) :
                            unitVal = "obo:UO_0000030"
                        if("minute" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            unitVal = "obo:UO_0000031"
                        if("hour" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            unitVal = "obo:UO_0000032"
                        if("day" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            unitVal = "obo:UO_0000033"
                        if("week" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            unitVal = "obo:UO_0000034"
                        if("month" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            unitVal = "obo:UO_0000035"
                        if("year" in (labelVal.lower() or commentVal.lower() or noteVal.lower())) :
                            unitVal = "obo:UO_0000036"
                        #---------------- good place to start improvements ----------------------
                        try:
                            best_match = unitMapper(labelVal, commentVal, noteVal, unit_label_list, unit_code_list)
                            if(best_match > 0):
                                unitVal = best_match
                            '''for unit_label in unit_label_list :
                                stemUnit = stemAll(unit_label.lower())
                                stemVal = stemAll(labelVal.lower() +" "+ commentVal.lower() +" "+ noteVal.lower())
                                if contains(stemUnit, stemVal) and len(stemUnit) > 0 :
                                    unit_index = unit_label_list.index(unit_label)
                                    unitVal = unit_uri_list[unit_index]
                                    if(contains(["in"] + stemUnit, stemVal)):
                                        break;
                            for unit_code in unit_code_list :
                                if len(unit_code) < 2 :
                                    continue
                                stemVal = stemAll(labelVal +" "+ commentVal +" "+ noteVal)
                                stemUnit = stemAll(unit_code)
                                if contains(stemUnit, stemVal) and len(stemUnit) > 0 :
                                    unit_index = unit_code_list.index(unit_code)
                                    unitVal = unit_uri_list[unit_index]
                                    if(contains(["in"] + stemUnit, stemVal)):
                                        break;
                                    #print unit_uri_list[unit_index]'''
                        except :
                            print "Something went wrong.."
                    except :
                        # Don't update unitVal
                        pass
                        #unitVal = ""
                    try :
                        timeVal = ""
                    except :
                        # Don't update timeVal
                        pass
                        #timeVal = ""
                    try :
                        entityVal = ""
                    except :
                        # Don't update entityVal
                        pass
                        #entityVal = ""
                    try :
                        relationVal = ""
                    except :
                        # Don't update relationVal
                        pass
                        #relationVal = ""
                    try :
                        inRelationToVal = ""
                    except :
                        # Don't update inrelationToVal
                        pass
                        #inRelationToVal = ""
                    try :
                        wasDerivedFromVal = ""
                    except :
                        # Don't update wasDerivedFromVal
                        pass
                        #wasDerivedFromVal = ""
                    try :
                        wasGeneratedByVal = ""
                    except :
                        # Don't update wasGeneratedByVal
                        pass
                        #wasGeneratedByVal = ""
                    try :
                        hasPositionVal = ""
                    except :
                        # Don't update hasPositionVal
                        pass
                        #hasPositionVal = ""

                    sdd.write(columnVal + "," + labelVal + "," + commentVal + "," + noteVal + "," + targetVal + "," + attributeVal + "," + attributeOfVal + "," + unitVal + "," + timeVal + "," + entityVal + "," + roleVal + "," + relationVal + "," + inRelationToVal + "," + wasDerivedFromVal + "," + wasGeneratedByVal + "," + hasPositionVal + "\n")
                    
                    tables = entry.findAll("table")
                    # Insert Codebook Entries
                    for table in tables :
                        table_rows = table.find("tbody").findAll("tr")
                        for table_row in table_rows :
                            codebook.write(entry.find("dl").find("dt",text="Variable Name: ").findNext("dd").contents[0].replace(" ","") + "," + table_row.find("td",scope="row").contents[0].encode('ascii','ignore').decode('utf-8') + ',"' + table_row.find("td",scope="row").findNext("td").contents[0].encode('ascii','ignore').decode('utf-8').replace("\"","'") + '"\n')
                sdd.close()
                codebook.close()
            except:
                print "\t\tNo codebook found for document"
    print ""

# demographics_link = "https://wwwn.cdc.gov" + soup.find("a",text="Demographics").get("href")
# print demographics_link
# demographics_soup = BeautifulSoup(requests.get(demographics_link).text, "lxml")
# #print demographics_soup.prettify()[0:1000]
# demographics_variable_link = "https://wwwn.cdc.gov/nchs/nhanes/search/" + demographics_soup.find("span",id="lblVarlist").findNext("a").get("href")
# print demographics_variable_link
# demographics_variable_soup = BeautifulSoup(requests.get(demographics_variable_link).text, "lxml")
# #print demographics_variable_soup.prettify()[0:1000]
# demographics_doc_rows = demographics_soup.find("table",id="GridView1").find("tbody").findAll("tr")
# for row in demographics_doc_rows:
#     if not (row.find("a").get("href") is "#"):
#         demographics_doc_link = "https://wwwn.cdc.gov" + row.find("a").get("href")
#         print demographics_doc_link
#         demographics_doc_soup = BeautifulSoup(requests.get(demographics_doc_link).text, "lxml")
#         entries=demographics_doc_soup.find("div", id="Codebook").findAll("div")
#         for entry in entries :
#             #print "Column: " + entry.find("dl").find("dt",text="Variable Name: ").findNext("dd").contents[0]
#             #print "label: " + entry.find("dl").find("dt",text="SAS Label: ").findNext("dd").contents[0]
#             tables = entry.findAll("table")
#             for table in tables :
#                 table_rows = table.find("tbody").findAll("tr")
#                 for table_row in table_rows :
#                     print entry.find("dl").find("dt",text="Variable Name: ").findNext("dd").contents[0] + "," + table_row.find("td",scope="row").contents[0] + "," + table_row.find("td",scope="row").findNext("td").contents[0]


# dietary_link = "https://wwwn.cdc.gov" + soup.find("a",text="Dietary").get("href")
# print dietary_link
# dietary_soup = BeautifulSoup(requests.get(dietary_link).text, "lxml")
# #print dietary_soup.prettify()[0:1000]
# dietary_variable_link = "https://wwwn.cdc.gov/nchs/nhanes/search/" + dietary_soup.find("span",id="lblVarlist").findNext("a").get("href")
# print dietary_variable_link
# dietary_variable_soup = BeautifulSoup(requests.get(dietary_variable_link).text, "lxml")
# #print dietary_variable_soup.prettify()[0:1000]
# dietary_doc_rows = dietary_soup.find("table",id="GridView1").find("tbody").findAll("tr")
# for row in dietary_doc_rows:
#     if not (row.find("a").get("href") is "#"):
#         dietary_doc_link = "https://wwwn.cdc.gov" + row.find("a").get("href")
#         print dietary_doc_link
#         dietary_doc_soup = BeautifulSoup(requests.get(dietary_doc_link).text, "lxml")


# examination_link = "https://wwwn.cdc.gov" + soup.find("a",text="Examination").get("href")
# print examination_link
# examination_soup = BeautifulSoup(requests.get(examination_link).text, "lxml")
# #print examination_soup.prettify()[0:1000]
# examination_variable_link = "https://wwwn.cdc.gov/nchs/nhanes/search/" + examination_soup.find("span",id="lblVarlist").findNext("a").get("href")
# print examination_variable_link
# examination_variable_soup = BeautifulSoup(requests.get(examination_variable_link).text, "lxml")
# #print examination_variable_soup.prettify()[0:1000]
# examination_doc_rows = examination_soup.find("table",id="GridView1").find("tbody").findAll("tr")
# for row in examination_doc_rows:
#     if not (row.find("a").get("href") is "#"):
#         examination_doc_link = "https://wwwn.cdc.gov" + row.find("a").get("href")
#         print examination_doc_link
#         examination_doc_soup = BeautifulSoup(requests.get(examination_doc_link).text, "lxml")
 
 
# laboratory_link = "https://wwwn.cdc.gov" + soup.find("a",text="Laboratory").get("href")
# print laboratory_link
# laboratory_soup = BeautifulSoup(requests.get(laboratory_link).text, "lxml")
# #print laboratory_soup.prettify()[0:1000]
# laboratory_variable_link = "https://wwwn.cdc.gov/nchs/nhanes/search/" + laboratory_soup.find("span",id="lblVarlist").findNext("a").get("href")
# print laboratory_variable_link
# laboratory_variable_soup = BeautifulSoup(requests.get(laboratory_variable_link).text, "lxml")
# #print laboratory_variable_soup.prettify()[0:1000]
# laboratory_doc_rows = laboratory_soup.find("table",id="GridView1").find("tbody").findAll("tr")
# for row in laboratory_doc_rows:
#     if not (row.find("a").get("href") is "#"):
#         laboratory_doc_link = "https://wwwn.cdc.gov" + row.find("a").get("href")
#         print laboratory_doc_link
#         laboratory_doc_soup = BeautifulSoup(requests.get(laboratory_doc_link).text, "lxml")


# questionnaire_link = "https://wwwn.cdc.gov" + soup.find("a",text="Questionnaire").get("href")
# print questionnaire_link
# questionnaire_soup = BeautifulSoup(requests.get(questionnaire_link).text, "lxml")
# #print questionnaire_soup.prettify()[0:1000]
# questionnaire_variable_link = "https://wwwn.cdc.gov/nchs/nhanes/search/" + questionnaire_soup.find("span",id="lblVarlist").findNext("a").get("href")
# print questionnaire_variable_link
# questionnaire_variable_soup = BeautifulSoup(requests.get(questionnaire_variable_link).text, "lxml")
# #print questionnaire_variable_soup.prettify()[0:1000]
# questionnaire_doc_rows = questionnaire_soup.find("table",id="GridView1").find("tbody").findAll("tr")
# for row in questionnaire_doc_rows:
#     if not (row.find("a").get("href") is "#"):
#         questionnaire_doc_link = "https://wwwn.cdc.gov" + row.find("a").get("href")
#         print questionnaire_doc_link
#         questionnaire_doc_soup = BeautifulSoup(requests.get(questionnaire_doc_link).text, "lxml")


# limited_access_link= "https://wwwn.cdc.gov" + soup.find("a",text="Limited Access").get("href")
# print limited_access_link
# limited_access_soup = BeautifulSoup(requests.get(limited_access_link).text, "lxml")
# #print limited_access_soup.prettify()[0:1000]
# limited_access_variable_link = "https://wwwn.cdc.gov/nchs/nhanes/search/" + limited_access_soup.find("span",id="lblVarlist").findNext("a").get("href")
# print limited_access_variable_link
# limited_access_variable_soup = BeautifulSoup(requests.get(limited_access_variable_link).text, "lxml")
# #print limited_access_variable_soup.prettify()[0:1000]
# limited_access_doc_rows = limited_access_soup.find("table",id="GridView1").find("tbody").findAll("tr")
# for row in limited_access_doc_rows:
#     if not (row.find("a").get("href") is "#"):
#         limited_access_doc_link = "https://wwwn.cdc.gov" + row.find("a").get("href")
#         print limited_access_doc_link
#         limited_access_doc_soup = BeautifulSoup(requests.get(limited_access_doc_link).text, "lxml")
