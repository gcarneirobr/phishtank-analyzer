import json, requests, pprint, hashlib, psycopg2, sys, os, base64, time

MAX_RETRIES_SITES = 3
MAX_RETRIES_JSON = 10
DSN = "host='postgres' dbname='phishtank' user='root' password='toor'"
URL_PHISHTANK = 'http://data.phishtank.com/data/d13a110a290419da26da6f9088c6f18ecd2cedc4636a451e76a97841828cd6c3/online-valid.json'

dictColumns = {'phish_id' : 0, 'url' : 1, 'online' : 2, 'target' : 3, 'submission_time' : 4, 'verified' : 5,
                    'verification_time' : 6, 'hash' : 7, 'details_ip_address' : 8, 'details_cidr_block' : 9,
                    'detail_time' : 10, 'details_rir' : 11, 'details_announcing_network' : 12, 'crawler_verified': 13}
TEST = False

conn = psycopg2.connect(DSN)
cur = conn.cursor()

def getJsonPhishtank():

    if TEST: 
        return True, mockJson()

    retries = 0
    getConnection = False
    conteudo = ''
    pprint.pprint("Recuperando JSON do Phishtank")

    while retries < MAX_RETRIES_JSON and not getConnection:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
            }
            pprint.pprint("Início da tentativa")
            r = requests.get(url=URL_PHISHTANK, headers=headers, timeout=600)
            if r.status_code == 200:
                conteudo = r.json()
                getConnection = True
            else:
                retries += 1
            pprint.pprint("Fim da tentativa - Status: %s" %  r.status_code)
        except requests.ConnectionError as ce:
            pprint.pprint(str(ce))
            retries += 1
        except requests.RequestException as re:
            retries += 1
            pprint.pprint(str(re))
        except:
            pprint.pprint("Erro!")
            retries += 1

    if not getConnection:
        pprint.pprint("Falha ao recuperar JSON")
        return False, ''
    else:
        pprint.pprint("JSON Recuperado")
        return True, conteudo

def getPhishingFromDatabase(columns):
    
    query = 'select %s from phish where valid_until is null'
    cur.execute(query %  columns)
    rows = cur.fetchall()

    return rows

def processJson(json, rows):
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
    columns = 'phish_id, url, online, target, submission_time, verified, verification_time, hash, details_ip_address, details_cidr_block, detail_time, details_rir, details_announcing_network, crawler_verified'
    phishingList = getPhishingFromDatabase(columns) 

    for phishing in phishingList: 
        currentSiteData = getCurrentDataFromSite(phishing[dictColumns['url']])
        
        if (phishing[dictColumns['online']] != currentSiteData['online']) or (phishing[dictColumns['hash']] != currentSiteData['hash']):
            storeChanges(phishing, currentSiteData)
    
def storeChanges(phishing, currentData):
    if phishing[dictColumns['crawler_verified']]:
        pprint.pprint ("-------------------")
        pprint.pprint("Registrando mudanças id: %s" % phishing[dictColumns['phish_id']])
        pprint.pprint("Database online: %s, Database hash: %s" % (phishing[dictColumns['online']], phishing[dictColumns['hash']]))
        pprint.pprint("Atual online: %s, Atual hash: %s" % (currentData['online'], currentData['hash'])
        
        updateSql = 'update phish set valid_until = now() where phish_id = %s and valid_until is null'
        insertSql = ('insert into phish (id, phish_id, url, '
                    ' submission_time, verified, verification_time, online, target, '
                    ' details_ip_address, details_cidr_block, details_announcing_network, details_rir, detail_time, hash, crawler_verified)'
                    ' values '
                    ' (nextval(\'phish_sequence\'), %s, %s, %s, %s, %s, %s, %s,  '
                    ' %s, %s, %s, %s, %s, %s, true)')
        
        data = (phishing[dictColumns['phish_id']], phishing[dictColumns['url']], phishing[dictColumns['submission_time']],
                phishing[dictColumns['verified']], phishing[dictColumns['verification_time']], currentData['online'], phishing[dictColumns['target']],
                phishing[dictColumns['details_ip_address']], phishing[dictColumns['details_cidr_block']], phishing[dictColumns['details_announcing_network']],
                phishing[dictColumns['details_rir']], phishing[dictColumns['detail_time']], 
                currentData['hash'] if currentData['online'] == phishing[dictColumns['online']] and currentData['hash'] != None else phishing[dictColumns['hash']])

        cur.execute(updateSql, (phishing[dictColumns['phish_id']],))
        conn.commit()
        cur.execute(insertSql, data)
        conn.commit()
    else: 
        updateSql = 'update phish set hash = %s, online = %s, crawler_verified = true where phish_id = %s'
        cur.execute(updateSql, (currentData['hash'], currentData['online'], phishing[dictColumns['phish_id']]))
        conn.commit()

def getCurrentDataFromSite(urlPhishing):
    result = {}
    content = ''
    result['online'], content = crawlSite(urlPhishing)
    
    if (result['online']):
        result['hash'] = hashContent(content)
    else: 
        result['hash'] = None

    pprint.pprint("hash = %s" % result['hash'])
    return result


def storeJsonData(output): 
    with open('data %s.json' % time.ctime(), 'w') as outfile:
        json.dump(output, outfile)

def crawlSite(url): 
    retries = 0
    getConnection = False
    conteudo = ''
    pprint.pprint("---------------------")
    pprint.pprint("Recuperando site %s" % url)
    while retries < MAX_RETRIES_SITES and not getConnection:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
            }
            r = requests.get(url=url, headers=headers, timeout=1)
            conteudo = r.text.encode()
            pprint.pprint(url)
            #pprint.pprint(conteudo)
            pprint.pprint(r.status_code)
            if r.status_code == 200:
                getConnection = True
            else: 
                retries += 1
        except requests.ConnectionError:
            retries += 1
        except requests.RequestException:
            retries += 1

    if not getConnection:
        return False, None
    else:
        return True, conteudo

def hashContent(sourceCode): 


    contentEncoded = base64.b64encode(sourceCode)
    hash_obj = hashlib.sha1(contentEncoded)
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

        with open(path, 'w') as mock:
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
