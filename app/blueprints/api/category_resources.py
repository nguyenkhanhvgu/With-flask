"""
Category resources for the API
"""

from flask import request
from flask_restful import Resource
from app.models import Category
from app.extensions import db
from .base import BaseResource, token_required, admin_required, category_to_dict


class CategoryListResource(BaseResource):
    """Resource for handling categories"""
    
    def get(self):
        """Get list of all categories"""
        try:
            categories = Category.query.order_by(Category.name).all()
            return {
                'categories': [category_to_dict(category) for category in categories]
            }, 200
            
        except Exception as e:
            return {'error': f'Failed to fetch categories: {str(e)}'}, 500
    
    @token_required
    @admin_required
    def post(self):
        """Create a new category (admin only)"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'No data provided'}, 400
            
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            
            if not name:
                return {'error': 'Category name is required'}, 400
            
            # Check if category already exists
            if Category.query.filter_by(name=name).first():
                return {'error': 'Category already exists'}, 400
            
            # Create category
            category = Category(name=name, description=description)
            db.session.add(category)
            db.session.commit()
            
            return {
                'message': 'Category created successfully',
                'category': category_to_dict(category)
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create category: {str(e)}'}, 500