CREATE USER jupyter WITH PASSWORD 'jupyter';
CREATE DATABASE jupyter;
GRANT ALL PRIVILEGES ON DATABASE jupyter TO jupyter;

CREATE USER hive WITH PASSWORD 'hive';
CREATE DATABASE metastore;
GRANT ALL PRIVILEGES ON DATABASE metastore TO hive;

SELECT 'GRANT SELECT,INSERT,UPDATE,DELETE ON "' || schemaname || '"."' || tablename || '" TO hive ;'
FROM pg_tables
WHERE tableowner = CURRENT_USER and schemaname = 'public';