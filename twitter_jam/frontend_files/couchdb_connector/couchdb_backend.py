#
# Team 43, Melbourne
# Aidan McLoughney(1030836)
# Thanaboon Muangwong(1049393)
# Nahid Tajik(1102790)
# Saket Khandelwal (1041999)
# Shmuli Bloom(982837)
#

import couchdb
import json
import logging

def db_instance(url):
    dbName = 'twt_db'
    try:
        #TODO: use remote url address instead of the localhost
        server = couchdb.Server(url)
        db = server[dbName]
    except Exception as e:
        logging.exception(e)
    return db

def query_view(db,fields,view,design_doc):
    docs = []
    count = 0
    try:
        for data in db.view(f'_design/{design_doc}/_view/{view}'):  # startkey=["Apr 29"], endkey=["May 02"]
            doc = {}
            doc['id'] = data.id
            doc['created_at'] = data.key
            for i,value in enumerate(data.value):
                doc[fields[i]] = value

            if doc['city']:
                doc['city'] = 'perth' if 'perth' in doc['city'] else doc['city']

            docs.append(doc)
            count += 1
        print("Total number of tweets related to the view: ", count)
    except Exception as e:
      print(e)
    
    return docs
