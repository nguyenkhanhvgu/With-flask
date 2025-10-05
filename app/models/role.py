"""
Role and Permission Models

This module contains models for Role-Based Access Control (RBAC).
It demonstrates many-to-many relationships, permission systems,
and security patterns in Flask applications.
"""

from app.extensions import db
from app.models.base import BaseModel


# Association table for many-to-many relationship between roles and permissions
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
    # Add indexes for performance
    db.Index('idx_role_permissions_role', 'role_id'),
    db.Index('idx_role_permissions_permission', 'permission_id')
)


class Permission(BaseModel):
    """
    Permission model for defining system permissions.
    
    This model demonstrates:
    - Simple permission definition
    - Many-to-many relationships with roles
    - Permission-based access control patterns
    - System permission management
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    
    # Table-level constraints
    __table_args__ = (
        # Ensure permission names are unique and not empty
        db.CheckConstraint("name != ''", name='permission_name_not_empty'),
    )
    
    @classmethod
    def get_by_name(cls, name):
        """
        Get permission by name.
        
        Args:
            name (str): Permission name to search for
            
        Returns:
            Permission or None: Permission if found, None otherwise
        """
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def create_default_permissions(cls):
        """
        Create default system permissions.
        
        This method demonstrates how to set up initial system permissions
        and is typically called during application setup or migrations.
        """
        default_permissions = [
            ('read_posts', 'Can read blog posts'),
            ('create_posts', 'Can create blog posts'),
            ('edit_own_posts', 'Can edit own blog posts'),
            ('edit_all_posts', 'Can edit any blog post'),
            ('delete_own_posts', 'Can delete own blog posts'),
            ('delete_all_posts', 'Can delete any blog post'),
            ('create_comments', 'Can create comments'),
            ('edit_own_comments', 'Can edit own comments'),
            ('edit_all_comments', 'Can edit any comment'),
            ('delete_own_comments', 'Can delete own comments'),
            ('delete_all_comments', 'Can delete any comment'),
            ('moderate_comments', 'Can moderate comments'),
            ('manage_categories', 'Can manage post categories'),
            ('manage_users', 'Can manage user accounts'),
            ('view_analytics', 'Can view site analytics'),
            ('admin_access', 'Full administrative access'),
            ('api_access', 'Can access API endpoints'),
            ('upload_files', 'Can upload files'),
            ('manage_roles', 'Can manage roles and permissions'),
            ('send_notifications', 'Can send notifications to users'),
        ]
        
        created_permissions = []
        for name, description in default_permissions:
            permission = cls.query.filter_by(name=name).first()
            if not permission:
                permission = cls(name=name, description=description)
                db.session.add(permission)
                created_permissions.append(permission)
        
        if created_permissions:
            db.session.commit()
        
        return created_permissions
    
    def __repr__(self):
        """String representation of the Permission object."""
        return f'<Permission {self.name}>'


class Role(BaseModel):
    """
    Role model for grouping permissions.
    
    This model demonstrates:
    - Role-based access control implementation
    - Many-to-many relationships with permissions
    - Hierarchical role systems
    - Default role management
    - Permission checking methods
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    is_default = db.Column(db.Boolean, default=False, index=True)
    
    # Relationships
    permissions = db.relationship('Permission',
                                secondary=role_permissions,
                                lazy='subquery',
                                backref=db.backref('roles', lazy=True))
    
    users = db.relationship('User', backref='role', lazy=True)
    
    # Table-level constraints
    __table_args__ = (
        # Ensure role names are unique and not empty
        db.CheckConstraint("name != ''", name='role_name_not_empty'),
        
        # Ensure only one default role exists
        db.Index('idx_role_default_unique', 'is_default', 
                postgresql_where=db.text('is_default = true')),
    )
    
    def add_permission(self, permission):
        """
        Add a permission to this role.
        
        Args:
            permission (Permission): Permission to add
            
        Returns:
            bool: True if permission was added, False if already exists
        """
        if not self.has_permission(permission):
            self.permissions.append(permission)
            return True
        return False
    
    def remove_permission(self, permission):
        """
        Remove a permission from this role.
        
        Args:
            permission (Permission): Permission to remove
            
        Returns:
            bool: True if permission was removed, False if not found
        """
        if self.has_permission(permission):
            self.permissions.remove(permission)
            return True
        return False
    
    def has_permission(self, permission):
        """
        Check if this role has a specific permission.
        
        Args:
            permission (Permission): Permission to check
            
        Returns:
            bool: True if role has permission, False otherwise
        """
        return permission in self.permissions
    
    def has_permission_by_name(self, permission_name):
        """
        Check if this role has a permission by name.
        
        Args:
            permission_name (str): Name of permission to check
            
        Returns:
            bool: True if role has permission, False otherwise
        """
        return any(p.name == permission_name for p in self.permissions)
    
    def get_permission_names(self):
        """
        Get list of permission names for this role.
        
        Returns:
            list: List of permission names
        """
        return [p.name for p in self.permissions]
    
    @classmethod
    def get_by_name(cls, name):
        """
        Get role by name.
        
        Args:
            name (str): Role name to search for
            
        Returns:
            Role or None: Role if found, None otherwise
        """
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_default_role(cls):
        """
        Get the default role for new users.
        
        Returns:
            Role: The default role
        """
        return cls.query.filter_by(is_default=True).first()
    
    @classmethod
    def create_default_roles(cls):
        """
        Create default system roles with appropriate permissions.
        
        This method demonstrates how to set up a role hierarchy
        and is typically called during application setup.
        """
        # Ensure permissions exist first
        Permission.create_default_permissions()
        
        # Define default roles and their permissions
        role_definitions = {
            'Guest': {
                'description': 'Anonymous users with minimal access',
                'permissions': ['read_posts'],
                'is_default': False
            },
            'User': {
                'description': 'Regular registered users',
                'permissions': [
                    'read_posts', 'create_posts', 'edit_own_posts', 'delete_own_posts',
                    'create_comments', 'edit_own_comments', 'delete_own_comments',
                    'upload_files'
                ],
                'is_default': True
            },
            'Moderator': {
                'description': 'Users who can moderate content',
                'permissions': [
                    'read_posts', 'create_posts', 'edit_own_posts', 'delete_own_posts',
                    'create_comments', 'edit_own_comments', 'delete_own_comments',
                    'edit_all_comments', 'delete_all_comments', 'moderate_comments',
                    'upload_files', 'view_analytics'
                ],
                'is_default': False
            },
            'Editor': {
                'description': 'Users who can edit all content',
                'permissions': [
                    'read_posts', 'create_posts', 'edit_own_posts', 'edit_all_posts',
                    'delete_own_posts', 'create_comments', 'edit_own_comments',
                    'delete_own_comments', 'edit_all_comments', 'delete_all_comments',
                    'moderate_comments', 'manage_categories', 'upload_files',
                    'view_analytics', 'api_access'
                ],
                'is_default': False
            },
            'Administrator': {
                'description': 'Full system administrators',
                'permissions': [
                    'read_posts', 'create_posts', 'edit_own_posts', 'edit_all_posts',
                    'delete_own_posts', 'delete_all_posts', 'create_comments',
                    'edit_own_comments', 'delete_own_comments', 'edit_all_comments',
                    'delete_all_comments', 'moderate_comments', 'manage_categories',
                    'manage_users', 'view_analytics', 'admin_access', 'api_access',
                    'upload_files', 'manage_roles', 'send_notifications'
                ],
                'is_default': False
            }
        }
        
        created_roles = []
        for role_name, role_data in role_definitions.items():
            role = cls.query.filter_by(name=role_name).first()
            if not role:
                # Create new role
                role = cls(
                    name=role_name,
                    description=role_data['description'],
                    is_default=role_data['is_default']
                )
                db.session.add(role)
                db.session.flush()  # Flush to get the role ID
                
                # Add permissions to role
                for permission_name in role_data['permissions']:
                    permission = Permission.get_by_name(permission_name)
                    if permission:
                        role.add_permission(permission)
                
                created_roles.append(role)
            else:
                # Update existing role permissions if needed
                existing_permissions = set(role.get_permission_names())
                required_permissions = set(role_data['permissions'])
                
                # Add missing permissions
                for permission_name in required_permissions - existing_permissions:
                    permission = Permission.get_by_name(permission_name)
                    if permission:
                        role.add_permission(permission)
        
        if created_roles:
            db.session.commit()
        
        return created_roles
    
    def __repr__(self):
        """String representation of the Role object."""
        return f'<Role {self.name}>'