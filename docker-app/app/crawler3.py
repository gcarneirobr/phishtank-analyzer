import pprint, json

with open('data.txt', 'r') as outfile: 
    jsonList = json.load(outfile)

print len(jsonList)

count = 0
countTotal = 0

type(jsonList)

for entry in jsonList: 
    #pprint.pprint(entry)
    countTotal = countTotal + 1
    print countTotal
    if entry['online'] == 'yes':
        print entry['phish_id']
        print entry['url']
        count = count + 1
#pprint.pprint(lines[0])

print count