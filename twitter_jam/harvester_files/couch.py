#
# Team 43, Melbourne
# Aidan McLoughney(1030836)
# Thanaboon Muangwong(1049393)
# Nahid Tajik(1102790)
# Saket Khandelwal (1041999)
# Shmuli Bloom(982837)
#

import couchdb
import contextlib

class Couch(object):
    def __init__(self,config,dbName,logger):
        self.logger = logger
        self.dbName = dbName
        try:
            self.server = couchdb.Server(config['URL'])  #TODO: use remote url address instead of the localhost
            self.logger.info("Created CouchDB server instance...")
            if dbName not in self.server:
                self.db = self.server.create(dbName)
                logger.info(f"{dbName} has been created!")
            else:
                self.db = self.server[dbName]
                logger.info(f"{dbName} exists!")
        except Exception as e:
            logger.exception(e)

    def save(self,data):
        # Trying to update an existing document with an incorrect _rev will raise a ResourceConflict exception.
        try:
            data['_id'] = data['id_str']
            doc_id, _ = self.db.save(data)
            self.logger.debug(f"{doc_id} Saved sucessfully......")
            return True
        except couchdb.http.ResourceConflict:
            self.logger.info(f"{data['id_str']} already exists.....")
            return False
        except Exception as e:
            self.logger.exception(e)
            return False