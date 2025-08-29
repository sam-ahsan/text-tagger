class AuthContext:
    def __init__(self, user_id: str, tenant: str):
        self.user_id = user_id
        self.tenant = tenant
