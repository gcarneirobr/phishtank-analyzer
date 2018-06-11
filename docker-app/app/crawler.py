import json, requests, pprint, hashlib, psycopg2, sys, os

MAX_RETRIES_SITES = 3
MAX_RETRIES_JSON = 10
DSN = "host='postgres' dbname='phishtank' user='root' password='toor'"
URL_PHISHTANK = 'http://data.phishtank.com/data/d13a110a290419da26da6f9088c6f18ecd2cedc4636a451e76a97841828cd6c3/online-valid.json'

TEST = True

conn = psycopg2.connect(DSN)
cur = conn.cursor()

def getJsonPhishtank():

    if TEST: 
        return True, mockJson()
  
    retries = 0
    getConnection = False
    conteudo = ''
    while retries < MAX_RETRIES_JSON or getConnection:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
            }
            r = requests.get(url=URL_PHISHTANK, headers=headers, timeout=2)
            conteudo = r.json
            if r.status_code == 200:
                getConnection = True
        except requests.ConnectionError:
            retries += 1
        except requests.RequestException:
            retries += 1
        except:
            retries += 1
    if not getConnection:
        return False, ''
    else:
        return True, conteudo

def getPhishingFromDatabase(columns):
    
    query = 'select %s from phish where valid_until is null'
    cur.execute(query %  columns)
    rows = cur.fetchall()

    return rows

def processJson(json, rows):
    pprint.pprint(rows)

    for phishing in json:
        if not (int(phishing['phish_id']),) in rows:
            storePhishing(phishing)
    

def storePhishing(phishing):
    insertSql = ('insert into phish (id, phish_id, url, '
                  ' submission_time, verified, verification_time, online, target, '
                  ' details_ip_address, details_cidr_block, details_announcing_network, details_rir, detail_time, hash, valid_until)'
                  ' values '
                  ' (nextval(\'phish_sequence\'), %s, %s, %s, %s, %s, %s, %s,  '
                  ' %s, %s, %s, %s,  %s, %s, %s)')

    data = (phishing['phish_id'], phishing['url'], phishing['submission_time'],
            phishing['verified'], phishing['verification_time'], True, phishing['target'],
            phishing['details'][0]['ip_address'], phishing['details'][0]['cidr_block'], phishing['details'][0]['announcing_network'],
            phishing['details'][0]['rir'], phishing['details'][0]['detail_time'], None, None)

    cur.execute(insertSql, data)
    conn.commit()

def processDatabase():
    columns = 'phish_id, online, target, submission_time, verified, verification_time, hash, details_ip_address, details_cidr_block'
    phishingList = getPhishingFromDatabase(columns) 
    
    for phishing in phishingList: 
        
        currentSiteData = getCurrentDataFromSite(phishing)
        
        if (phishing['online'] != currentSiteData['online']) or (phishing['hash'] != currentSiteData['hash']):
            storeChanges(phishing, currentSiteData)
    
def storeChanges(phishing, currentData):

    if phishing['hash'] is not None:
        updateSql = 'update phish set valid_until = now() where phish_id = %s and valid_until is null'
        insertSql = ('insert into phish (id, phish_id, url, '
                    ' submission_time, verified, verification_time, online, target, '
                    ' details_ip_address, details_cidr_block, details_announcing_network, details_rir, detail_time, hash)'
                    ' values '
                    ' (nextval(\'phish_sequence\'), %s, \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\',  '
                    ' \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', %s')
        
        data = (phishing['phish_id'], phishing['url'], phishing['submission_time'],
                phishing['verified'], phishing['verification_time'], currentData['online'], phishing['target'],
                phishing['details'][0]['ip_address'], phishing['details'][0]['cidr_block'], phishing['details'][0]['announcing_network'],
                phishing['details'][0]['rir'], phishing['details'][0]['detail_time'], currentData['hash'])

        cur.execute(updateSql, phishing['phish_id'])
        conn.commit()
        cur.execute(insertSql, data)
        conn.commit()
    else: 
        updateSql = 'update phish set hash = %s where phish_id = %s'
        cur.execute(updateSql, (currentData['hash'], phishing['phish_id']))
        conn.commit()


def getCurrentDataFromSite(phishing):
    result = {}
    content = ''
    result['online'], content = crawlSite(phishing['url'])
    result['hash'] = hashContent(content)

    return result


def storeJsonData(output): 
    with open('data.txt', 'w') as outfile:
        json.dump(output, outfile)

def crawlSite(url): 
    retries = 0
    getConnection = False
    conteudo = ''
    while retries < MAX_RETRIES_SITES or getConnection:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
            }
            r = requests.get(url=URL_PHISHTANK, headers=headers, timeout=1)
            conteudo = r.text.encode()
            if r.status_code == 200:
                getConnection = True
        except requests.ConnectionError:
            retries += 1
        except requests.RequestException:
            retries += 1
            retries += 1
    if not getConnection:
        return False, None
    else:
        return True, conteudo

def hashContent(sourceCode): 
    hash_obj = hashlib.sha256(sourceCode)
    hash = hash_obj.hexdigest()

    return hash

def mockJson():

    path = './mock.json'

    if not (os.path.exists(path) and os.path.getsize(path)):
        with open('data.json', 'r') as data:
            jsonData = json.load(data)
        entries = []

        for jsonEntry in jsonData[:100]:
            entries.append(jsonEntry)

        with open(path,'w') as mock:
            json.dump(entries, mock)

    with open(path) as mockFile:
        mockData = json.load(mockFile)

    return mockData

def main():

    phishingList = getPhishingFromDatabase('phish_id')
    connect, currentJson = getJsonPhishtank()

    status = 1
    if connect: 
        storeJsonData(currentJson)
        processJson(currentJson, phishingList)
        processDatabase()
        status = 0 
    return status

if __name__ == '__main__':
    status = main()

