from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

class DBService:
    def __init__(self):
        load_dotenv()
        mongodb_uri=os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_URI is not set in the .env file")
        self.client = MongoClient(mongodb_uri)
        self.db = self.client["test_database_3"]
        self.collection = self.db["test_collection"]

    def add_document(self, document):
        result = self.collection.insert_one(document)
        return result.inserted_id
    
    def document_exists(self, document_id):
        return self.collection.find_one({"id": document_id}) is not None
    
    def find_document_by_he_id(self, he_id):
        return self.collection.find_one({"heIdentifier": he_id})
    
    def update_document(self, he_id, preparatory_id, submissions):
        result = self.collection.update_one(
            {"heIdentifier": he_id},
            {"$set": {"preparatoryIdentifier": preparatory_id, "submissions": submissions}}
        )
        return result.modified_count
    
    def clean_identifiers(self):
        regex = r" vp$"
        documents = self.collection.find({"heIdentifier": {"$regex": regex}})
        updated_count = 0

        for doc in documents:
            identifier = doc["heIdentifier"]
            new_identifier = re.sub(regex, "", identifier)
            print(f"{identifier} -> {new_identifier}")
            self.collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"heIdentifier": new_identifier}}
            )
            updated_count += 1

        print(f"Päivitetty {updated_count} dokumenttia")

    def create_search_index(self):
        existing_indexes = self.collection.list_indexes()
        index_exists = any(
            idx["key"] == {"name": "text", "heIdentifier": "text", "preparatoryIdentifier": "text", "proposalContent": "text"}
            for idx in existing_indexes
        )
        if not index_exists:
            self.collection.create_index([("name", "text"), ("heIdentifier", "text"), ("preparatoryIdentifier", "text"), ("proposalContent", "text")])
            print("Tekstihakemisto luotu.")
        else:
            print("Tekstihakemisto on jo olemassa.")

