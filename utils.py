import inflect
import re

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