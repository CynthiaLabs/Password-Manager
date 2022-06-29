import base64
import pathlib
import os
import json

import bcrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

from pw_manager.utils import errors
from pw_manager.utils import utils, constants
from pw_manager.db_entry import DatabaseEntry


"""
File structure of database.db:

{
    "salt": "some_salt",
    "content": "Giant_encrypted_blob_of_text"
}


"""


class Database:
    def __init__(self, path: str, password: str):
        self.path = path
        self.password = password

        self.salt: bytes = bytes()

        self.content: list[DatabaseEntry] = list()

    # ====================== Database functions =================================

    def create(self) -> None:
        """
        Creates a database with the path and password given in the constructor
        """
        path = pathlib.Path(self.path)
        if not path.parent.exists():
            raise errors.DirectoryDoesNotExistException

        self.salt = bcrypt.gensalt()

        if os.path.exists(self.path):
            raise errors.DatabaseAlreadyFoundException

        content = {
            "salt": self.salt.decode(),
            "content": "[]"
        }

        content["content"] = self.encrypt_content(content["content"])

        with open(self.path, "w+") as f:
            json.dump(content, f, indent=2)

        utils.add_db_path_to_cache(str(path.absolute()))

    def read(self) -> None:
        """
        Reads the database with the password and salt of this db
        """
        path = pathlib.Path(self.path)

        if not path.exists():
            raise errors.DatabasePathDoesNotExistException

        with open(str(path.absolute())) as f:
            db_content: dict = json.load(f)

        self.salt = db_content.get("salt").encode()

        raw_list = json.loads(self.decrypt_content(db_content.get("content")))

        for entry in raw_list:
            self.content.append(DatabaseEntry(website_or_usage=entry.get("website_or_usage"),
                                              username=entry.get("username"),
                                              description=entry.get("description"),
                                              password=entry.get("password")))

        constants.db_file = self

    def write(self) -> None:
        """
        Writes the database to file
        """
        path = pathlib.Path(self.path)

        if not path.exists():
            raise errors.DatabasePathDoesNotExistException

        with open(str(path.absolute())) as f:
            db_content: dict = json.load(f)

        raw_data = []

        for entry in self.content:
            raw_data.append({
                "website_or_usage": entry.website_or_usage,
                "username": entry.username,
                "description": entry.description,
                "password": entry.password
            })

        with open(str(path.absolute()), "w") as f:
            db_content["salt"] = self.salt.decode()

            db_content["content"] = self.encrypt_content(json.dumps(raw_data))

            json.dump(db_content, f, indent=2)

    def add_database_entry(self, website_or_usage: str, description: str, username: str, password: str, should_write: bool = True) -> None:
        """
        Adds a database entry
        :param website_or_usage: The website or usage
        :param description: The description
        :param username: The username
        :param password: The password
        :param should_write: If we should write to disk
        """

        self.content.append(DatabaseEntry(website_or_usage=website_or_usage, description=description, username=username, password=password))

        if should_write:
            self.write()

    def get_all_entries(self) -> list[DatabaseEntry]:
        """
        Gets all entries
        :return: A list of all entries
        """
        return self.content

    def update_entry(self, old_entry: DatabaseEntry, new_entry: DatabaseEntry, should_write: bool = True) -> None:
        """
        Updates an entry
        :param old_entry: The old entry
        :param new_entry: The updated entry
        :param should_write: If we should write to disk
        """

        index = self.content.index(old_entry)
        self.content[index] = new_entry

        if should_write:
            self.write()

    def delete_entry(self, entry: DatabaseEntry, should_write: bool = True) -> None:
        """
        Deletes an entry
        :param entry: Entry to delete
        :param should_write: If we should write to disk
        """

        self.content.pop(self.content.index(entry))

        if should_write:
            self.write()

    # ======================= Encryption stuff =====================================

    def __gen_fernet_key__(self) -> bytes:
        """
        Generates a key using the password and salt of this db
        :return: Key in bytes
        """
        byte_password = self.password.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512_256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )

        return base64.urlsafe_b64encode(kdf.derive(byte_password))

    def encrypt_content(self, content: str) -> str:
        """
        Encrypts the string given with the password and salt of this db
        :param content: String to encrypt
        :return: Encrypted string
        """
        fernet = Fernet(self.__gen_fernet_key__())
        encrypted_data = fernet.encrypt(content.encode())

        return encrypted_data.decode()

    def decrypt_content(self, content: str) -> str:
        """
        Decrypts the string given with the password and salt of this db
        :param content: String to decrypt
        :return: Decrypted String
        """
        fernet = Fernet(self.__gen_fernet_key__())
        decrypted_data = fernet.decrypt(content.encode())

        return decrypted_data.decode()
