from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Admin model
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def _repr_(self):
        return f'<Admin id={self.id} username={self.username}>'

# Service model
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    # Relationships
    professionals = db.relationship('ServiceProfessional', backref='service', cascade='all, delete', lazy=True)
    requests = db.relationship('ServiceRequest', backref='service', cascade='all, delete', lazy=True)

# ServiceProfessional model
class ServiceProfessional(db.Model):
    __tablename__ = 'service_professionals'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    fullname = db.Column(db.String(128), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    document = db.Column(db.String(256), nullable=False)
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    rating = db.Column(db.Float, nullable=True)  # Float for average ratings

    # Rating validator
    @staticmethod
    def validate_rating(rating):
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5 stars.")

    # Relationships
    requests = db.relationship('ServiceRequest', backref='professional', cascade='all, delete', lazy=True)

# Customer model
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(128), nullable=False)
    fullname = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(64), nullable=False, unique=True)
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(10), nullable=False)

    # Relationships
    requests = db.relationship('ServiceRequest', backref='customer', cascade='all, delete', lazy=True)

# ServiceRequest model
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id', ondelete='SET NULL'), nullable=True)
    date_of_request = db.Column(db.DateTime, default=datetime)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    service_status = db.Column(db.String(32), nullable=False, default='requested')
    is_request_edited = db.Column(db.Boolean, nullable=False, default= False)

