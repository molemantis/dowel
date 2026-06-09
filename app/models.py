import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    share_token = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

    tools = db.relationship('Tool', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    icon = db.Column(db.String(64), default='🔧')

    tools = db.relationship('Tool', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Tool(db.Model):
    __tablename__ = 'tools'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    name = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(64))
    model_number = db.Column(db.String(64))
    serial_number = db.Column(db.String(64))
    year_purchased = db.Column(db.Integer)
    condition = db.Column(db.String(16), default='good')  # excellent/good/fair/poor
    description = db.Column(db.Text)
    specs = db.Column(db.JSON)
    image_filename = db.Column(db.String(256))
    retailer_url = db.Column(db.String(512))
    source = db.Column(db.String(16), default='uploaded')  # homedepot/lowes/uploaded/url
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    checkouts = db.relationship('Checkout', backref='tool', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='tool', lazy='dynamic')

    @property
    def active_checkout(self):
        return self.checkouts.filter_by(returned_at=None).first()

    @property
    def is_available(self):
        return self.active_checkout is None

    def __repr__(self):
        return f'<Tool {self.name}>'


class Checkout(db.Model):
    __tablename__ = 'checkouts'
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    borrower_name = db.Column(db.String(120), nullable=False)
    borrower_email = db.Column(db.String(120))
    borrower_phone = db.Column(db.String(32))
    checked_out_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    checkout_duration_days = db.Column(db.Integer, default=7)

    def __repr__(self):
        return f'<Checkout {self.tool_id} to {self.borrower_name}>'


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    guest_name = db.Column(db.String(120))
    guest_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(16), default='pending')  # pending/notified/fulfilled/cancelled

    user = db.relationship('User', backref='reservations')

    def __repr__(self):
        return f'<Reservation {self.tool_id}>'
