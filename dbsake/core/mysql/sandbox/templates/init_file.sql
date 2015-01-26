-- Initialize the requested database user

GRANT ALL PRIVILEGES ON *.* TO '{{user|escape_string}}'@'{{host|escape_string}}' IDENTIFIED BY '{{password|escape_string}}' WITH GRANT OPTION;
