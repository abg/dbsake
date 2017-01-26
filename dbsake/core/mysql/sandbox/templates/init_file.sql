-- Initialize the requested database user

{% if dist.version < (5, 7, 6) or 'MariaDB' in dist.version.comment %}
-- Lock out non-local root users by default
UPDATE mysql.user SET Password = '*THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE' Where User = 'root' AND Host <> 'localhost';
{% else %}
-- Lock out non-local root users by default
UPDATE mysql.user SET account_locked = 'Y'  Where User = 'root' AND Host <> 'localhost';
{% endif %}

GRANT ALL PRIVILEGES ON *.* TO '{{ user|escape_string }}'@'{{ host|escape_string }}' IDENTIFIED BY '{{ password|escape_string }}' WITH GRANT OPTION;
{% if user != "root" %}
-- Reset root@localhost, if we are adding a non-standard user
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' IDENTIFIED BY '{{ password|escape_string }}' WITH GRANT OPTION;
{% endif %}
