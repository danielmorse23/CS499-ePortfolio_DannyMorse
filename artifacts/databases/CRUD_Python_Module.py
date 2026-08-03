"""
CS 499 Computer Science Capstone!
Category Three: Databases

Artifact: Animal Shelter Dashboard 
Original Course: CS 340 Client/Server Development
Original Creation Date: November 2025
Enhancements Date: July 27 - Aug 2, 2026
Student: Danny Morse

Overview:
This mod provides create, read, update, and delete operations
for records of animals that are stored in a MongoDB. 

Enhancement Summary:
The original CRUD functionality was retained and expanded to improve upon four
main things:
    1. security
    2. reliability
    3. validation
    4. maintainability

The enhanced module supports DB settings through:
    - environment variables
    - allows local testing without hardcoded credentials
    - validates incoming data
    - provides more clear error messages when actions fail 
    - prevents empty update/delete filters from accidentally affecting the entire DB

Some other enhancements include:
    - optional sorting and result limits,
    - record counting
    - database connection testing
    - safer MongoDB update operations
    - logging
    - proper connection cleaning  

Outcome Alignment:
This enhancement demonstrates progress toward using tools and
DB techniques to create a more reliable and secure program. It also touches upon
a stronger security mindset by reducing exposed credentials, validating inputs
and protecting records from unsafe DB actions
"""

import logging
import os
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError


# Shows basic messages when a database action works or fails
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


class AnimalShelter:
    """Handles the MongoDB actions used by the Dashboard"""

    # Required when adding a new animal record
    REQUIRED_ANIMAL_FIELDS = ("animal_type", "breed")

    def __init__(self):
        """
        Sets up the DB connection, the connection information can be changed
        through environment variables instead of editing the source code every time now.
        """

        self.settings = {
            "username": os.getenv("AAC_USER"),
            "password": os.getenv("AAC_PASSWORD"),
            "host": os.getenv("AAC_HOST", "localhost"),
            "port": int(os.getenv("AAC_PORT", "27017")),
            "database": os.getenv("AAC_DATABASE", "aac"),
            "collection": os.getenv("AAC_COLLECTION", "animals_test"),
            "auth_source": os.getenv("AAC_AUTH_SOURCE", "admin")
        }

        self._validate_credentials()

        # Uses authentication for provided login info
        if self.settings["username"] and self.settings["password"]:
            safe_username = quote_plus(self.settings["username"])
            safe_password = quote_plus(self.settings["password"])

            mongo_uri = (
                f"mongodb://{safe_username}:{safe_password}@"
                f"{self.settings['host']}:{self.settings['port']}/"
                f"?authSource={self.settings['auth_source']}"
            )

        # Connects without authentication for local testing
        else:
            mongo_uri = (
                f"mongodb://{self.settings['host']}:"
                f"{self.settings['port']}"
            )

        self.client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000
        )

        self.database = self.client[self.settings["database"]]
        self.collection = self.database[self.settings["collection"]]

    def _validate_credentials(self):
        """
        Allows local testing without a login, but requires both login
        values if authentication is going to be used.
        """

        username_exists = bool(self.settings["username"])
        password_exists = bool(self.settings["password"])

        if username_exists != password_exists:
            raise ValueError(
                "Provide both AAC_USER and AAC_PASSWORD, or leave both unset for a local connection."
            )

    @staticmethod
    def _require_dictionary(value, description):
        """Makes sure DB info is passed as a dict."""

        if not isinstance(value, dict):
            raise TypeError(f"{description} must be a dictionary!")

    @staticmethod
    def _prevent_empty_filter(filter_data, operation_name):
        """
        Stops an update/delete from accidentally affecting every single animal record
        """

        if not filter_data:
            raise ValueError(
                f"{operation_name} requires a nonempty filter, otherwise it could affect the entire collection!"
            )

    def _validate_animal_record(self, data):
        # Checks a new animal record before adding it to MongoDB 

        self._require_dictionary(data, "Animal data")

        if not data:
            raise ValueError("Data cant be empty!")

        missing_fields = [
            field
            for field in self.REQUIRED_ANIMAL_FIELDS
            if not data.get(field)
        ]

        if missing_fields:
            missing_text = ", ".join(missing_fields)

            raise ValueError(
                f"Animal record is missing the required information: "
                f"{missing_text}"
            )

    def check_connection(self):
        # Checks whether the program can connecto to the DB

        try:
            self.client.admin.command("ping")
            logger.info("MongoDB connection was successful!")
            return True

        except ServerSelectionTimeoutError as connection_error:
            logger.error(
                "MongoDB did not respond before timing out: %s",
                connection_error
            )
            return False

        except PyMongoError as connection_error:
            logger.error(
                "MongoDB connection failed: %s",
                connection_error
            )
            return False

    def create(self, data):
        # Adds one animal record to the DB

        self._validate_animal_record(data)

        try:
            insert_result = self.collection.insert_one(data)

            if insert_result.acknowledged:
                logger.info(
                    "Animal record created with ID %s.",
                    insert_result.inserted_id
                )
                return True

            return False

        except PyMongoError as create_error:
            logger.error(
                "Animal record could not be created: %s",
                create_error
            )
            return False

    def read(self, query=None, projection=None, sort_by=None, limit=0):
        """
        Searches the database for animal records where the search can also choose 
        certain fields, sort the results, or simply limit the number returns
        """

        if query is None:
            query = {}

        self._require_dictionary(query, "Read query")

        if projection is not None:
            self._require_dictionary(projection, "Projection")

        if sort_by is not None and not isinstance(sort_by, str):
            raise TypeError("Must be a string or none!")

        if not isinstance(limit, int) or limit < 0:
            raise ValueError(
                "The result must be a positive number"
            )

        try:
            records = self.collection.find(query, projection)

            if sort_by:
                records = records.sort(sort_by, 1)

            if limit > 0:
                records = records.limit(limit)

            return list(records)

        except PyMongoError as read_error:
            logger.error(
                "Records could not be retrieved: %s",
                read_error
            )
            return []

    def count(self, query=None):
        # Counts how many animal records match search critera

        if query is None:
            query = {}

        self._require_dictionary(query, "Count query")

        try:
            return self.collection.count_documents(query)

        except PyMongoError as count_error:
            logger.error(
                "Animal records cant be counted: %s",
                count_error
            )
            return 0

    def update(self, filter_data, update_data):
        
        # Updates animal records that match the filter

        self._require_dictionary(filter_data, "Update filter")
        self._require_dictionary(update_data, "Update data")
        self._prevent_empty_filter(filter_data, "Update")

        if not update_data:
            raise ValueError("Update data cannot be empty.")

        # Checks whether the update already contains a cmd
        uses_operator = any(
            str(key).startswith("$")
            for key in update_data
        )

        if uses_operator:
            contains_regular_field = any(
                not str(key).startswith("$")
                for key in update_data
            )

            if contains_regular_field:
                raise ValueError(
                    "MongoDB update ops can't be mixed with regular field names."
                )

            prepared_update = update_data

        else:
            prepared_update = {"$set": update_data}

        try:
            update_result = self.collection.update_many(
                filter_data,
                prepared_update
            )

            logger.info(
                "%s animal record(s) matched; %s record(s) modified.",
                update_result.matched_count,
                update_result.modified_count
            )

            return update_result.modified_count

        except PyMongoError as update_error:
            logger.error(
                "Animal records couldn't be updated: %s",
                update_error
            )
            return 0

    def delete(self, filter_data):
        # Deletes animal records that match the filter request

        self._require_dictionary(filter_data, "Delete filter")
        self._prevent_empty_filter(filter_data, "Delete")

        try:
            delete_result = self.collection.delete_many(filter_data)

            logger.info(
                "%s animal record(s) deleted.",
                delete_result.deleted_count
            )

            return delete_result.deleted_count

        except PyMongoError as delete_error:
            logger.error(
                "Animal records couldn't be deleted: %s",
                delete_error
            )
            return 0

    def close(self):
        # Closes the DB connection when it is no longer needed

        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # Automatically closes the connection 
        self.close()