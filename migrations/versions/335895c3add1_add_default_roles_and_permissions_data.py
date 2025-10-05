"""Add default roles and permissions data

Revision ID: 335895c3add1
Revises: 93b4357aa44a
Create Date: 2025-10-05 10:15:03.219291

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '335895c3add1'
down_revision = '93b4357aa44a'
branch_labels = None
depends_on = None


def upgrade():
    """
    Populate default permissions and roles for the RBAC system.
    
    This migration demonstrates:
    - Data migrations in Flask-Migrate
    - Setting up default system permissions
    - Creating role hierarchy with appropriate permissions
    - Ensuring data consistency and referential integrity
    """
    # Get table references for data insertion
    permission_table = sa.table('permission',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    
    role_table = sa.table('role',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('is_default', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime)
    )
    
    role_permissions_table = sa.table('role_permissions',
        sa.column('role_id', sa.Integer),
        sa.column('permission_id', sa.Integer)
    )
    
    # Current timestamp for created_at and updated_at
    now = datetime.utcnow()
    
    # Define default permissions
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
    
    # Insert permissions only if they don't exist
    # First check if permissions already exist
    connection = op.get_bind()
    existing_permissions = connection.execute(
        sa.text("SELECT name FROM permission")
    ).fetchall()
    existing_permission_names = {row[0] for row in existing_permissions}
    
    permission_data = []
    permission_name_to_id = {}
    
    # If no permissions exist, insert all with sequential IDs
    if not existing_permissions:
        for i, (name, description) in enumerate(default_permissions, 1):
            permission_data.append({
                'id': i,
                'name': name,
                'description': description,
                'created_at': now,
                'updated_at': now
            })
            permission_name_to_id[name] = i
        
        if permission_data:
            op.bulk_insert(permission_table, permission_data)
    else:
        # If permissions exist, get their IDs and only insert missing ones
        existing_permission_data = connection.execute(
            sa.text("SELECT id, name FROM permission")
        ).fetchall()
        
        for row in existing_permission_data:
            permission_name_to_id[row[1]] = row[0]
        
        # Find the next available ID
        max_id = max(permission_name_to_id.values()) if permission_name_to_id else 0
        
        # Insert only missing permissions
        for name, description in default_permissions:
            if name not in existing_permission_names:
                max_id += 1
                permission_data.append({
                    'id': max_id,
                    'name': name,
                    'description': description,
                    'created_at': now,
                    'updated_at': now
                })
                permission_name_to_id[name] = max_id
        
        if permission_data:
            op.bulk_insert(permission_table, permission_data)
    
    # Define default roles and their permissions
    role_definitions = {
        'Guest': {
            'id': 1,
            'description': 'Anonymous users with minimal access',
            'permissions': ['read_posts'],
            'is_default': False
        },
        'User': {
            'id': 2,
            'description': 'Regular registered users',
            'permissions': [
                'read_posts', 'create_posts', 'edit_own_posts', 'delete_own_posts',
                'create_comments', 'edit_own_comments', 'delete_own_comments',
                'upload_files'
            ],
            'is_default': True
        },
        'Moderator': {
            'id': 3,
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
            'id': 4,
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
            'id': 5,
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
    
    # Insert roles
    role_data = []
    for role_name, role_info in role_definitions.items():
        role_data.append({
            'id': role_info['id'],
            'name': role_name,
            'description': role_info['description'],
            'is_default': role_info['is_default'],
            'created_at': now,
            'updated_at': now
        })
    
    # Insert roles only if they don't exist
    existing_roles = connection.execute(
        sa.text("SELECT name FROM role")
    ).fetchall()
    existing_role_names = {row[0] for row in existing_roles}
    
    roles_to_insert = []
    for role_name, role_info in role_definitions.items():
        if role_name not in existing_role_names:
            roles_to_insert.append({
                'id': role_info['id'],
                'name': role_name,
                'description': role_info['description'],
                'is_default': role_info['is_default'],
                'created_at': now,
                'updated_at': now
            })
    
    if roles_to_insert:
        op.bulk_insert(role_table, roles_to_insert)
    
    # Insert role-permission relationships only for new roles
    role_permission_data = []
    for role_name, role_info in role_definitions.items():
        if role_name not in existing_role_names:
            role_id = role_info['id']
            for permission_name in role_info['permissions']:
                if permission_name in permission_name_to_id:
                    permission_id = permission_name_to_id[permission_name]
                    role_permission_data.append({
                        'role_id': role_id,
                        'permission_id': permission_id
                    })
    
    if role_permission_data:
        op.bulk_insert(role_permissions_table, role_permission_data)


def downgrade():
    """
    Remove default roles and permissions data.
    
    This demonstrates proper cleanup in migration downgrades,
    ensuring the database can be rolled back to previous state.
    """
    # Delete role-permission relationships first (foreign key constraints)
    op.execute("DELETE FROM role_permissions")
    
    # Delete roles
    role_names = ['Guest', 'User', 'Moderator', 'Editor', 'Administrator']
    for role_name in role_names:
        op.execute(f"DELETE FROM role WHERE name = '{role_name}'")
    
    # Delete permissions
    permission_names = [
        'read_posts', 'create_posts', 'edit_own_posts', 'edit_all_posts',
        'delete_own_posts', 'delete_all_posts', 'create_comments',
        'edit_own_comments', 'edit_all_comments', 'delete_own_comments',
        'delete_all_comments', 'moderate_comments', 'manage_categories',
        'manage_users', 'view_analytics', 'admin_access', 'api_access',
        'upload_files', 'manage_roles', 'send_notifications'
    ]
    
    for permission_name in permission_names:
        op.execute(f"DELETE FROM permission WHERE name = '{permission_name}'")
