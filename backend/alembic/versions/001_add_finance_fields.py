"""add finance fields and backfill nulls

Revision ID: 001_add_finance_fields
Revises:
Create Date: 2026-08-31 02:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_add_finance_fields"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("scheme_rules"):
        op.create_table(
            "scheme_rules",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column(
                "payment_frequency", sa.String(), nullable=True, server_default=sa.text("'monthly'")
            ),
            sa.Column("moratorium_interest_treatment", sa.String(), nullable=True),
            sa.Column("working_capital_percent", sa.Float(), nullable=True),
        )
    else:
        columns_sr = [c["name"] for c in inspector.get_columns("scheme_rules")]
        if "payment_frequency" not in columns_sr:
            op.add_column(
                "scheme_rules",
                sa.Column(
                    "payment_frequency",
                    sa.String(),
                    nullable=True,
                    server_default=sa.text("'monthly'"),
                ),
            )
        if "moratorium_interest_treatment" not in columns_sr:
            op.add_column(
                "scheme_rules",
                sa.Column("moratorium_interest_treatment", sa.String(), nullable=True),
            )
        if "working_capital_percent" not in columns_sr:
            op.add_column(
                "scheme_rules", sa.Column("working_capital_percent", sa.Float(), nullable=True)
            )

    if not inspector.has_table("repayment_schedules"):
        op.create_table(
            "repayment_schedules",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("remaining_principal", sa.Float(), nullable=True),
            sa.Column("principal_amount", sa.Float(), nullable=True),
            sa.Column("opening_balance", sa.Float(), nullable=True),
            sa.Column(
                "verification_required",
                sa.Boolean(),
                nullable=True,
                server_default=sa.text("false"),
            ),
        )
    else:
        columns_rs = [c["name"] for c in inspector.get_columns("repayment_schedules")]
        if "opening_balance" not in columns_rs:
            op.add_column(
                "repayment_schedules", sa.Column("opening_balance", sa.Float(), nullable=True)
            )
        if "verification_required" not in columns_rs:
            op.add_column(
                "repayment_schedules",
                sa.Column(
                    "verification_required",
                    sa.Boolean(),
                    nullable=True,
                    server_default=sa.text("false"),
                ),
            )

    # 3. Intelligent batch backfill SQL for existing null rows
    op.execute(
        "UPDATE repayment_schedules SET opening_balance = CASE WHEN remaining_principal IS NOT NULL THEN remaining_principal + COALESCE(principal_amount, 0) ELSE 0.0 END WHERE opening_balance IS NULL;"
    )
    op.execute(
        "UPDATE scheme_rules SET payment_frequency = 'monthly' WHERE payment_frequency IS NULL;"
    )
    op.execute(
        "UPDATE repayment_schedules SET verification_required = false WHERE verification_required IS NULL;"
    )


def downgrade() -> None:
    op.drop_column("repayment_schedules", "verification_required")
    op.drop_column("repayment_schedules", "opening_balance")
    op.drop_column("scheme_rules", "working_capital_percent")
    op.drop_column("scheme_rules", "moratorium_interest_treatment")
    op.drop_column("scheme_rules", "payment_frequency")
