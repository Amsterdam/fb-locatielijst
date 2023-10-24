# Wait to be sure that SQL Server came up
# Run the setup script to create the DB and the schema in the DB
# Note: make sure that your password matches what is in the Dockerfile
# /opt/mssql-tools/bin/sqlcmd -S localhost -U $SA_USER -P $SA_PASSWORD -d master -i setup.sql
until /opt/mssql-tools/bin/sqlcmd -U $SA_USER -P $SA_PASSWORD -i setup.sql; do echo retry && sleep 1; done