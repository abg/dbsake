-- Secure database during bootstrap by removing anonymous users
-- and setting a password

-- Note: This is used by dbsake's mysqld --bootstrap run and no statement
-- should span more than one line.
-- See /usr/share/mysql/mysql_system_tables*.sql for more complex examples of
-- what can be added here.

USE mysql;
DELETE FROM `db` WHERE (Db = 'test' OR Db = 'test\_%') AND User = '';
DELETE FROM `user` WHERE User = '';
UPDATE `user` SET PASSWORD = PASSWORD('{{password|escape}}') WHERE User = 'root';
