class DatabaseEntry:
    def __init__(self, website_or_usage: str, username: str, description: str, password: str):
        self.website_or_usage = website_or_usage
        self.username = username
        self.description = description
        if not isinstance(description, str):
            raise AttributeError("AHH WARUM KEIN STRING")
        self.password = password

    def __eq__(self, other):
        if not isinstance(other, DatabaseEntry):
            return False
        return self.website_or_usage == other.website_or_usage and self.username == other.username and self.description == other.description and self.password == other.password

    def __ge__(self, other):
        if not isinstance(other, DatabaseEntry):
            return False

        return self.website_or_usage >= other.website_or_usage

    def __lt__(self, other):
        if not isinstance(other, DatabaseEntry):
            return False

        return self.website_or_usage < other.website_or_usage
