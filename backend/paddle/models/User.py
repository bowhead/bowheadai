from flask_login import UserMixin

users = {}

class User(UserMixin):
    id = None
    username = 'tmp'
    
    def __init__(self, id):
        users[id] = 1
        self.id = id
    
    def get_id(self):
        return self.id