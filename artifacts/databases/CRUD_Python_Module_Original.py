from pymongo import MongoClient 
from bson.objectid import ObjectId 

# Constructor for connection to MongoDB using animals collection
class AnimalShelter(object):
    # Sets up the login and DB
    def __init__(self):
        USER = 'aacuser'
        PASS = 'ABCD1234'
        HOST = 'localhost'
        PORT = 27017
        DB = 'aac'
        COL = 'animals'
        
        # Initialize Connection (authenticate against admin DB)
        self.client = MongoClient('mongodb://%s:%s@%s:%d/%s' % (USER, PASS, HOST, PORT, "admin"))
        self.database = self.client['%s' % DB]
        self.collection = self.database['%s' % COL]
            
    # Implements the C in CRUD
    def create(self, data):
        if data is not None and isinstance(data, dict):
            # Insert a document and it will return True/False if it worked
            try:
                result = self.collection.insert_one(data)
                return bool(result.acknowledged)
            except Exception:
                return False
        else:
            return False
            
    # Searches for docs that match a query (R in CRUD)
    def read(self, query):
        if query is not None and isinstance(query, dict):
            try:
                cursor = self.collection.find(query)
                return list(cursor)
            except Exception:
                return []
        else:
            return []
    # Update docs
    def update(self, filter_data, update_data):
      if not isinstance(filter_data, dict) or not isinstance(update_data,dict):
        raise TypeError("Both filter and update must be dictionaries.")

      try:
        outcome = self.collection.update_many(filter_data, update_data)
        return outcome.modified_count
      
      except Exception as update_error:

        print("Update has failed:", update_error)
        return 0

    # Delete docs
    def delete(self, filter_data):
    
        if not isinstance(filter_data, dict):
            raise TypeError("Needs to be a dictionary")

        try:
            result = self.collection.delete_many(filter_data)
            return result.deleted_count
        except Exception as delete_err:
            print("Deletion has failed:", delete_err)
            return 0



    


