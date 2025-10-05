"""
Base Model

This module contains the base model class that provides common functionality
for all database models. It demonstrates SQLAlchemy model inheritance patterns
and common model utilities.
"""

from datetime import datetime
from app.extensions import db


class BaseModel(db.Model):
    """
    Base model class that provides common functionality for all models.
    
    This class demonstrates:
    - SQLAlchemy model inheritance
    - Common timestamp fields
    - Utility methods for all models
    - Abstract base class pattern
    """
    
    # Make this an abstract base class
    __abstract__ = True
    
    # Common fields that all models should have
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """
        Save the current instance to the database.
        
        This method provides a convenient way to save model instances
        and demonstrates common database operation patterns.
        """
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """
        Delete the current instance from the database.
        
        This method provides a convenient way to delete model instances
        and demonstrates safe deletion patterns.
        """
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """
        Update the current instance with the provided keyword arguments.
        
        Args:
            **kwargs: Field names and values to update
            
        Returns:
            BaseModel: The updated instance
            
        This method demonstrates dynamic model updating and
        automatic timestamp handling.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Update the updated_at timestamp
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def to_dict(self):
        """
        Convert the model instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the model
            
        This method is useful for JSON serialization and API responses.
        It demonstrates model serialization patterns.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    @classmethod
    def create(cls, **kwargs):
        """
        Create a new instance of the model.
        
        Args:
            **kwargs: Field names and values for the new instance
            
        Returns:
            BaseModel: The created instance
            
        This method demonstrates the factory pattern for model creation
        and provides a convenient way to create and save instances.
        """
        instance = cls(**kwargs)
        return instance.save()
    
    @classmethod
    def get_by_id(cls, id):
        """
        Get a model instance by its ID.
        
        Args:
            id (int): The ID of the instance to retrieve
            
        Returns:
            BaseModel or None: The instance if found, None otherwise
            
        This method demonstrates common query patterns and
        provides a consistent interface for ID-based lookups.
        """
        return cls.query.get(id)
    
    @classmethod
    def get_or_404(cls, id):
        """
        Get a model instance by its ID or raise a 404 error.
        
        Args:
            id (int): The ID of the instance to retrieve
            
        Returns:
            BaseModel: The instance
            
        Raises:
            404: If the instance is not found
            
        This method demonstrates error handling patterns in Flask applications.
        """
        return cls.query.get_or_404(id)
    
    def __repr__(self):
        """
        String representation of the model instance.
        
        Returns:
            str: String representation showing the class name and ID
        """
        return f'<{self.__class__.__name__} {self.id}>'