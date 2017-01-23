-- Initialize the requested database user

{% if 'MariaDB' in dist.version.comment and dist.version >= (5, 2) %}
GRANT ALL PRIVILEGES ON *.* TO '{{ user|escape_string }}'@'{{ host|escape_string }}' IDENTIFIED VIA unix_socket;
{% elif dist.version >= (5, 5, 10) %}
GRANT ALL PRIVILEGES ON *.* to '{{ user|escape_string }}'@'{{ host|escape_string }}' IDENTIFIED WITH auth_socket;
{% else %}
GRANT ALL PRIVILEGES ON *.* TO '{{ user|escape_string }}'@'{{ host|escape_string }}' IDENTIFIED BY '{{ password|escape_string }}';
{% endif %}
