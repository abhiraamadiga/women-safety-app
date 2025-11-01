from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class IncidentReport(db.Model):
    """Store incident reports with AI analysis"""
    __tablename__ = 'incident_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User relationship (optional for anonymous reports)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=True)
    
    # Basic incident details
    who_involved = db.Column(db.String(100))
    who_sub_option = db.Column(db.String(100))
    incident_type = db.Column(db.String(100))
    incident_sub_type = db.Column(db.String(200))
    location = db.Column(db.String(100))
    location_detail = db.Column(db.String(200))
    
    # Impact details
    impact = db.Column(db.String(100))
    impact_detail_severity = db.Column(db.String(50))
    impact_detail_symptoms = db.Column(db.String(100))
    impact_detail_harm_type = db.Column(db.String(100))
    impact_detail_medical = db.Column(db.String(50))
    impact_detail_financial = db.Column(db.String(50))
    impact_detail_loss_type = db.Column(db.String(100))
    impact_detail_reputation = db.Column(db.String(100))
    impact_detail_ongoing = db.Column(db.String(100))
    impact_detail_fear_level = db.Column(db.String(50))
    impact_detail_fear_type = db.Column(db.String(100))
    impact_detail_sleep = db.Column(db.String(50))
    impact_detail_sleep_type = db.Column(db.String(100))
    impact_detail_other = db.Column(db.Text)
    
    # Time details
    incident_date = db.Column(db.Date)
    incident_time = db.Column(db.String(50))
    first_time = db.Column(db.String(10))
    frequency = db.Column(db.String(50))
    
    # Optional additional details
    additional_details = db.Column(db.Text)
    
    # AI Analysis
    ai_summary = db.Column(db.Text)
    
    # Community sharing
    posted_to_community = db.Column(db.Boolean, default=False)
    report_to_police = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<IncidentReport {self.id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'who_involved': self.who_involved,
            'incident_type': self.incident_type,
            'location': self.location,
            'impact': self.impact,
            'incident_date': self.incident_date.strftime('%Y-%m-%d') if self.incident_date else None,
            'ai_summary': self.ai_summary,
            'posted_to_community': self.posted_to_community,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class CommunityPost(db.Model):
    """Store community posts with reactions"""
    __tablename__ = 'community_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('incident_reports.id'), nullable=False)
    
    # User information (nullable for anonymous posts)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(50), nullable=True)  # Cached username or "Anonymous"
    is_anonymous = db.Column(db.Boolean, default=True)
    
    # Post content (from AI summary)
    story = db.Column(db.Text, nullable=False)
    
    # Reactions
    support_count = db.Column(db.Integer, default=0)
    hug_count = db.Column(db.Integer, default=0)
    solidarity_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    report = db.relationship('IncidentReport', backref=db.backref('community_post', uselist=False))
    user = db.relationship('User', backref=db.backref('posts', lazy=True), foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<CommunityPost {self.id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username if not self.is_anonymous else 'Anonymous',
            'is_anonymous': self.is_anonymous,
            'story': self.story,
            'support_count': self.support_count,
            'hug_count': self.hug_count,
            'solidarity_count': self.solidarity_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_active': self.is_active
        }


class Comment(db.Model):
    """Store comments on community posts"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('community_posts.id'), nullable=False)
    
    # User information (nullable for anonymous comments)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(50), nullable=True)  # Cached username or "Anonymous"
    is_anonymous = db.Column(db.Boolean, default=True)
    
    text = db.Column(db.Text, nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    post = db.relationship('CommunityPost', backref=db.backref('comments', lazy=True))
    user = db.relationship('User', backref=db.backref('comments', lazy=True), foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<Comment {self.id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username if not self.is_anonymous else 'Anonymous',
            'is_anonymous': self.is_anonymous,
            'text': self.text,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_active': self.is_active
        }


class EmergencyContact(db.Model):
    """Store emergency contacts for SOS alerts"""
    __tablename__ = 'emergency_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Contact details
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)  # Mother, Friend, Sibling, etc.
    
    # Priority order (1-4)
    priority = db.Column(db.Integer, default=1)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('emergency_contacts', lazy=True))
    
    def __repr__(self):
        return f'<EmergencyContact {self.name} for User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'relationship': self.relationship,
            'priority': self.priority
        }


class SOSAlert(db.Model):
    """Store SOS alert events and their status"""
    __tablename__ = 'sos_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Alert details
    trigger_time = db.Column(db.DateTime, default=datetime.utcnow)
    trigger_method = db.Column(db.String(50), default='button')  # button, shake, voice
    
    # Location at trigger
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_accuracy = db.Column(db.Float, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_pin_verified = db.Column(db.Boolean, default=False)
    
    # Recording details
    audio_recording_url = db.Column(db.String(500), nullable=True)
    video_recording_url = db.Column(db.String(500), nullable=True)
    
    # Alert sent status
    contacts_notified = db.Column(db.Integer, default=0)
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Battery level at trigger
    battery_level = db.Column(db.Integer, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('sos_alerts', lazy=True))
    
    def __repr__(self):
        return f'<SOSAlert {self.id} User {self.user_id} Active:{self.is_active}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'is_active': self.is_active,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contacts_notified': self.contacts_notified,
            'battery_level': self.battery_level,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
