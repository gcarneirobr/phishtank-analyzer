import json, requests, pprint


url = 'http://data.phishtank.com/data/d13a110a290419da26da6f9088c6f18ecd2cedc4636a451e76a97841828cd6c3/online-valid.json'


data = requests.get(url=url)
binary = data.content
output = json.loads(binary)

with open('data.txt', 'w') as outfile:
    json.dump(output, outfile)

# test to see if the request was valid
#print output['status']

# output all of the results
#pprint.pprint(output)

# step-by-step directions
for entry in output:
    print(entry['phish_id'])
    print(entry['url']) 
    print(entry['submission_time'])