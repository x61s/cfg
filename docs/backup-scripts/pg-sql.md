```
pg_dump \
  -h <postgres_host> \
  -p <port> \
  -U <username> \
  -d <database_name> \
  -F p \
  -f <backup_file.sql>
```
