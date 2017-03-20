-- don't write any bootstrap stuff to the binary log
-- even if it is enabled
SET @@session.sql_log_bin = 0;
CREATE DATABASE IF NOT EXISTS `mysql`;
USE mysql;

-- mysql_system_tables.sql start --
{{mysql_system_tables}}
{{mysql_performance_tables|default('')}}

-- mysql_system_tables.sql end --
{% if bootstrap_data %}
CREATE DATABASE IF NOT EXISTS `test`;
-- mysql_system_tables_data.sql start --
{{mysql_system_tables_data}}
-- mysql_system_tables_data.sql start --
-- fill_help_tables.sql start --
{{fill_help_tables}}
-- fill_help_tables.sql end --

-- Secure database during bootstrap by removing anonymous users
-- and setting a password

-- Note: This is used by dbsake's mysqld --bootstrap run and no statement
-- should span more than one line.
-- See /usr/share/mysql/mysql_system_tables*.sql for more complex examples of
-- what can be added here.

-- dbsake: cleanup system users start --
DELETE FROM `user` WHERE Host NOT IN ('localhost', '127.0.0.1', '::1');
DELETE FROM `user` WHERE User = '';
{# MySQL 5.7.6 removed the mysql.user (Password) column
   MySQL 5.7.2 requires plugin to be populated #}
{% if distribution.version.tag != "MariaDB" and distribution.version >= (5, 7) %}
UPDATE `user` SET plugin = 'mysql_native_password', authentication_string = CONCAT('*', UPPER(SHA1(UNHEX(SHA1('{{password|escape_string}}'))))) WHERE user = 'root';
{% else %}
UPDATE `user` SET PASSWORD = PASSWORD('{{password|escape_string}}') WHERE User = 'root';
{% endif %}
DELETE FROM `db` WHERE (Db = 'test' OR Db = 'test\_%') AND User = '';
-- dbsake: cleanup system users end --
{% endif %}
