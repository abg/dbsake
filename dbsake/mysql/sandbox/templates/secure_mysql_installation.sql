-- Secure database during bootstrap by removing anonymous users
-- and setting a password
USE mysql;
DELETE FROM `db`;
DELETE FROM `user` WHERE User <> 'root';
DELETE FROM `user` WHERE User = 'root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
UPDATE `user` SET PASSWORD = PASSWORD('{{password|escape}}') WHERE User = 'root';
