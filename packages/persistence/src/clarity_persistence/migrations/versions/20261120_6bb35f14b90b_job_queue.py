"""job queue

Revision ID: 6bb35f14b90b
Revises: 8c65eddbc4dd
"""

from collections.abc import Sequence

from alembic import op
from procrastinate import App, PsycopgConnector
from sqlalchemy.util import await_only

revision: str = "6bb35f14b90b"
down_revision: str | None = "8c65eddbc4dd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DROP_PROCRASTINATE = """
do $$
declare item record;
begin
  for item in select tablename from pg_tables
      where schemaname = 'public' and tablename like 'procrastinate%' loop
    execute format('drop table if exists %I cascade', item.tablename);
  end loop;
  for item in select p.oid::regprocedure as signature from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
      where n.nspname = 'public' and p.proname like 'procrastinate%' loop
    execute format('drop function if exists %s cascade', item.signature);
  end loop;
  for item in select t.typname from pg_type t
      join pg_namespace n on n.oid = t.typnamespace
      where n.nspname = 'public' and t.typname like 'procrastinate%'
        and t.typtype in ('c', 'e') loop
    execute format('drop type if exists %I cascade', item.typname);
  end loop;
end $$;
"""


def _execute_script(sql: str) -> None:
    driver = op.get_bind().connection.driver_connection
    if driver is None:
        raise RuntimeError("no driver connection")
    await_only(driver.execute(sql))


def upgrade() -> None:
    _execute_script(App(connector=PsycopgConnector()).schema_manager.get_schema())


def downgrade() -> None:
    _execute_script(DROP_PROCRASTINATE)
