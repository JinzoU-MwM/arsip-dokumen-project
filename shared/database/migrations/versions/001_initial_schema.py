"""Initial schema creation

Revision ID: 0001
Revises:
Create Date: 2024-10-22 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_role enum
    user_role_enum = postgresql.ENUM('admin', 'legal_admin', 'company_user', 'viewer', name='userrole')
    user_role_enum.create(op.get_bind())

    # Create user_status enum
    user_status_enum = postgresql.ENUM('active', 'inactive', 'suspended', name='userstatus')
    user_status_enum.create(op.get_bind())

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('salt', sa.String(length=255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('status', user_status_enum, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=True)

    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('npwp', sa.String(length=20), nullable=True),
        sa.Column('nib', sa.String(length=15), nullable=True),
        sa.Column('company_type', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('business_description', sa.Text(), nullable=True),
        sa.Column('compliance_requirements', sa.JSON(), nullable=True),
        sa.Column('notification_settings', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'])
    op.create_index(op.f('ix_companies_nib'), 'companies', ['nib'], unique=True)
    op.create_index(op.f('ix_companies_npwp'), 'companies', ['npwp'], unique=True)

    # Create document_status enum
    document_status_enum = postgresql.ENUM('uploaded', 'processing', 'processed', 'failed', 'validated', 'rejected', name='documentstatus')
    document_status_enum.create(op.get_bind())

    # Create compliance_status enum
    compliance_status_enum = postgresql.ENUM('compliant', 'non_compliant', 'partially_compliant', 'requires_review', name='compliancestatus')
    compliance_status_enum.create(op.get_bind())

    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('status', document_status_enum, nullable=True),
        sa.Column('processing_id', sa.String(length=100), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('extracted_entities', sa.JSON(), nullable=True),
        sa.Column('ai_analysis', sa.JSON(), nullable=True),
        sa.Column('compliance_status', compliance_status_enum, nullable=True),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('missing_documents', sa.JSON(), nullable=True),
        sa.Column('drive_file_id', sa.String(length=255), nullable=True),
        sa.Column('drive_folder_id', sa.String(length=255), nullable=True),
        sa.Column('drive_url', sa.String(length=500), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_document_type'), 'documents', ['document_type'])
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'])
    op.create_index(op.f('ix_documents_processing_id'), 'documents', ['processing_id'], unique=True)

    # Create processing_status enum
    processing_status_enum = postgresql.ENUM('queued', 'processing', 'completed', 'failed', 'cancelled', name='processingstatus')
    processing_status_enum.create(op.get_bind())

    # Create processing_jobs table
    op.create_table('processing_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processing_id', sa.String(length=100), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', processing_status_enum, nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('total_steps', sa.Integer(), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('cpu_usage', sa.Float(), nullable=True),
        sa.Column('memory_usage', sa.Float(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processing_jobs_processing_id'), 'processing_jobs', ['processing_id'], unique=True)

    # Create notification_status enum
    notification_status_enum = postgresql.ENUM('pending', 'sent', 'failed', 'retrying', name='notificationstatus')
    notification_status_enum.create(op.get_bind())

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=True),
        sa.Column('template_data', sa.JSON(), nullable=True),
        sa.Column('status', notification_status_enum, nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('processing_job_id', sa.Integer(), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_status', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['processing_job_id'], ['processing_jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'])
    op.create_index(op.f('ix_notifications_status'), 'notifications', ['status'])

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('resource_details', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sensitivity_level', sa.String(length=20), nullable=True),
        sa.Column('compliance_tags', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'])
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'])
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'])

    # Create system_configurations table
    op.create_table('system_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(length=100), nullable=False),
        sa.Column('config_value', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=True),
        sa.Column('validation_schema', sa.JSON(), nullable=True),
        sa.Column('allowed_values', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id)
    )
    op.create_index(op.f('ix_system_configurations_config_key'), 'system_configurations', ['config_key'], unique=True)

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_name', sa.String(length=100), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('allowed_endpoints', sa.JSON(), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_api_key'), 'api_keys', ['api_key'], unique=True)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('api_keys')
    op.drop_table('system_configurations')
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('processing_jobs')
    op.drop_table('documents')
    op.drop_table('companies')
    op.drop_table('users')

    # Drop enums
    postgresql.ENUM(name='notificationstatus').drop(op.get_bind())
    postgresql.ENUM(name='processingstatus').drop(op.get_bind())
    postgresql.ENUM(name='compliancestatus').drop(op.get_bind())
    postgresql.ENUM(name='documentstatus').drop(op.get_bind())
    postgresql.ENUM(name='userstatus').drop(op.get_bind())
    postgresql.ENUM(name='userrole').drop(op.get_bind())