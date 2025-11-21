from alembic import op
import sqlalchemy as sa
import geoalchemy2

# Revision identifiers, used by Alembic.
revision = '0001_create_incidents_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('incident_type', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('frame_urls', sa.JSON(), nullable=False),
        sa.Column('verification_status', sa.String(), nullable=True, default='pending'),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('incidents')