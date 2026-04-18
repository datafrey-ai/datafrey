"""PostHog event name constants."""

CLI_INVOKED = "cli.invoked"
CLI_COMPLETED = "cli.completed"

LOGIN_STARTED = "login.started"
LOGIN_COMPLETED = "login.completed"
LOGIN_FAILED = "login.failed"

DB_CONNECT_STARTED = "db.connect.started"
DB_CONNECT_PROVIDER_SELECTED = "db.connect.provider_selected"
DB_CONNECT_AUTH_SELECTED = "db.connect.auth_selected"
DB_CONNECT_SETUP_COMPLETED = "db.connect.setup_completed"
DB_CONNECT_CREDENTIALS_ENTERED = "db.connect.credentials_entered"
DB_CONNECT_REVIEW_SHOWN = "db.connect.review_shown"
DB_CONNECT_ABORTED = "db.connect.aborted"
DB_CONNECT_SUBMITTED = "db.connect.submitted"
DB_CONNECT_CONNECTED = "db.connect.connected"
DB_CONNECT_FAILED = "db.connect.failed"

INDEX_OFFERED = "index.offered"
INDEX_STARTED = "index.started"

CLIENT_MENU_SHOWN = "client.menu_shown"
CLIENT_SELECTED = "client.selected"
CLIENT_SETUP_COMPLETED = "client.setup_completed"
CLIENT_SETUP_FAILED = "client.setup_failed"
