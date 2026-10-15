# MySQL deployment path

Use **MySQL 8.4** and Python's optional connector. The application creates the schema through `sql/schema_mysql.sql`; do not change delimiters or split trigger SQL at semicolons. The Python initializer uses `-- statement` boundaries, so a trigger is sent as one statement.

## With Docker Desktop

```powershell
Copy-Item .env.example .env
# Edit MYSQL_PASSWORD and MYSQL_ROOT_PASSWORD. Set DB_BACKEND=mysql.
docker compose up -d mysql
docker compose ps
python -m pip install -r requirements-mysql.txt
python -m riskflow demo --backend mysql
python -m riskflow serve --backend mysql
```

The database binds only to `127.0.0.1:3306`. Credentials are loaded by Compose and by the Python application from the local `.env` file. If that port is occupied, change the host-side port in Compose and MYSQL_PORT in `.env`. Docker is optional; the SQLite demo works without it.

The dedicated demo server enables `log_bin_trust_function_creators` so its application user can create the audit trigger with binary logging enabled. For an existing server, ask its administrator to create the schema/trigger with appropriate privileges instead of changing global settings on an operational database. See [MySQL trigger privileges](https://dev.mysql.com/doc/refman/8.4/en/create-trigger.html).

## With an existing local server

Create a dedicated `riskflow` database and a local `riskflow` user with schema/view/trigger and DML privileges on that database. Use a unique local password. Put the host, port, username, database and password in `.env`; run the connector install and demo commands above. Do not point this prototype at an existing operational database: the pipeline replaces its own current-source/assessment tables.

## Verification

For a dedicated disposable test database, set `RISKFLOW_TEST_MYSQL=1` and run the test suite. The live integration test refreshes the demo tables and appends an analyst decision; it is intended only for a test database.

The GitHub Actions workflow already provisions an isolated MySQL 8.4 service, installs the connector and enables this test. It checks schema initialization, parameterized writes, a native audit trigger, replay preservation, evaluation and exports. No live MySQL service was available during the initial local build; consult the workflow's actual result after publication.

## Stop

Use `docker compose stop mysql` to stop the service while retaining its named volume. Resume with `docker compose start mysql`. Avoid removing the volume if you want to retain review history.

Reference: [MySQL Connector/Python](https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html).
