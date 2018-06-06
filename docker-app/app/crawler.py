import json, requests, pprint, hashlib

urlPhishtank = 'http://data.phishtank.com/data/d13a110a290419da26da6f9088c6f18ecd2cedc4636a451e76a97841828cd6c3/online-valid.json'

data = requests.get(url=urlPhishtank)
output = data.json

with open('data.txt', 'w') as outfile:
    json.dump(output, outfile)

for entry in output:
    siteCrawled = crawlSite(entry['url'])
    hash = hashSite(siteCrawled)
    
def crawlSite(url): 
    return requests.get(url).text

def hashSite(sourceCode): 
    hashObject = hashlib.sha256()