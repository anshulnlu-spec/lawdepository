# This is the new, corrected code

# Build the database URL for Cloud SQL (PostgreSQL)
# The drivername 'postgresql+psycopg2' tells SQLAlchemy how to talk to Postgres.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=db_user,
    password=db_password,
    database=db_name,
    query={"host": f"/cloudsql/{db_host}"},
)
