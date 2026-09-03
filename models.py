from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# -------------------------
# USER MODEL (Auth)
# -------------------------
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)


# -------------------------
# PATIENT MODEL
# -------------------------
class Patient(db.Model):
    __tablename__ = 'patient'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    age = db.Column(db.Float, nullable=False)
    bp = db.Column(db.Float, nullable=False)
    sg = db.Column(db.Float, nullable=False)
    alb = db.Column(db.Float, nullable=False)
    sugar = db.Column(db.Float, nullable=False)
    glucose = db.Column(db.Float, nullable=False)
    urea = db.Column(db.Float, nullable=False)
    creatinine = db.Column(db.Float, nullable=False)
    hb = db.Column(db.Float, nullable=False)

    # store 0/1 instead of string
    ht = db.Column(db.Integer, nullable=False)
    dm = db.Column(db.Integer, nullable=False)
    anemia = db.Column(db.Integer, nullable=False)

    result = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
