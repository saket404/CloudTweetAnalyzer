import couchdb


def db_connection(config, logger):
    databases = config['DBS'].split(",")
    try:
        couch = couchdb.Server('http://%s:%s@localhost:5984/' % (config['USERNAME'], config['PASSWORD']))  #TODO: use remote url address instead of the localhost
        logger.info("Connected to CouchDB...")
        for database in databases:
            if database not in couch:
                couch.create(database)
                logger.info(f"{database} has been created!")
            else:
                logger.info(f"{database} exists!")
    except:
        logger.exception("Could not connect to CouchDB!")
    return couch


def insert_data(data, dbName, logger):
        # Trying to update an existing document with an incorrect _rev will raise a ResourceConflict exception.
        try:
            data['_id'] = data['id_str']
            doc_id, _ = dbName.save(data)
            return True
        except couchdb.http.ResourceConflict:
            logger.debug(f"{data['id_str']} already exists.....")
            return False
        except Exception as e:
            logger.exception(e)
            return False