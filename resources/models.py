import uuid
from sqlalchemy.dialects.postgresql import UUID
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserAuth(db.Model):
    __tablename__ = "UserAuth"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    user_id = db.Column(db.String())
    u = db.Column(db.String())
    p = db.Column(db.String())
    
    def __init__(self, user_id, u, p):
        self.user_id = user_id
        self.u = u
        self.p = p
    
    def __repr__(self):
        return "<user_id {}>".format(self.user_id)