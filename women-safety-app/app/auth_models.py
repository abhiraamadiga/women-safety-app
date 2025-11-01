from app.models import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic info
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Optional profile info
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # Location & ID (all optional)
    home_city_district = db.Column(db.String(120))
    address = db.Column(db.String(255))

    # Appearance (structured)
    age_range = db.Column(db.String(50))
    gender_presentation = db.Column(db.String(50))
    height = db.Column(db.String(50))
    build = db.Column(db.String(50))
    hair = db.Column(db.String(120))
    clothing = db.Column(db.String(120))
    skin_tone = db.Column(db.String(80))
    distinctive_marks = db.Column(db.String(255))
    accessories = db.Column(db.String(255))
    photo_path = db.Column(db.String(255))  # Stored path to uploaded photo

    # Medical & identifying
    blood_group = db.Column(db.String(8))
    allergies = db.Column(db.String(255))
    chronic_conditions = db.Column(db.String(255))
    disability = db.Column(db.String(255))

    # Emergency contacts
    primary_contact_name = db.Column(db.String(120))
    primary_contact_phone = db.Column(db.String(30))
    secondary_contact = db.Column(db.String(120))
    
    # Account settings
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    emergency_pin_hash = db.Column(db.String(200))  # PIN for SOS deactivation
    
    # Privacy settings
    default_anonymous = db.Column(db.Boolean, default=True)  # Post anonymously by default
    consent_share_with_police = db.Column(db.Boolean, default=False)
    consent_share_photo_with_police = db.Column(db.Boolean, default=False)
    data_retention = db.Column(db.String(20), default='1y')  # 30d | 1y | indefinite
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    reports = db.relationship('IncidentReport', backref='user', lazy=True, foreign_keys='IncidentReport.user_id')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)
    
    def set_emergency_pin(self, pin):
        """Hash and set emergency PIN"""
        self.emergency_pin_hash = generate_password_hash(str(pin))
    
    def check_emergency_pin(self, pin):
        """Check if emergency PIN matches"""
        if not self.emergency_pin_hash:
            return False
        return check_password_hash(self.emergency_pin_hash, str(pin))
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'name': self.name,
            'phone': self.phone,
            'default_anonymous': self.default_anonymous,
            'home_city_district': self.home_city_district,
            'address': self.address,
            'age_range': self.age_range,
            'gender_presentation': self.gender_presentation,
            'height': self.height,
            'build': self.build,
            'hair': self.hair,
            'clothing': self.clothing,
            'skin_tone': self.skin_tone,
            'distinctive_marks': self.distinctive_marks,
            'accessories': self.accessories,
            'blood_group': self.blood_group,
            'allergies': self.allergies,
            'chronic_conditions': self.chronic_conditions,
            'disability': self.disability,
            'primary_contact_name': self.primary_contact_name,
            'primary_contact_phone': self.primary_contact_phone,
            'secondary_contact': self.secondary_contact,
            'consent_share_with_police': self.consent_share_with_police,
            'consent_share_photo_with_police': self.consent_share_photo_with_police,
            'data_retention': self.data_retention,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
