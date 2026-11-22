import secrets
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def now():
    # waktu lokal mesin (server jalan lokal), supaya statistik harian sesuai hari user
    return datetime.now()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(64), unique=True, index=True)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def new_token(self):
        self.token = secrets.token_hex(32)
        return self.token


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    minutes = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=now)

    subject = db.relationship("Subject")

    def to_dict(self):
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "subject": self.subject.name,
            "minutes": self.minutes,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.DateTime)
    done = db.Column(db.Boolean, default=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "done": self.done,
            "subject_id": self.subject_id,
        }


class ConceptMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    data = db.Column(db.Text, default='{"nodes": [], "edges": []}')
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def to_dict(self, with_data=True):
        d = {"id": self.id, "title": self.title, "updated_at": self.updated_at.isoformat()}
        if with_data:
            d["data"] = self.data
        return d
