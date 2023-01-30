class FrontendConfig:
    host: str = None
    uuid: str = None
    public_key: str = None

    def __init__(self, host: str, uuid: str, public_key: str):
        self.host = host
        self.uuid = uuid
        self.public_key = public_key

    def get_host(self):
        return self.host

    def get_uuid(self):
        return self.uuid

    def get_public_key(self):
        return self.public_key