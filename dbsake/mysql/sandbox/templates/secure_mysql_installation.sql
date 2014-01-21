-- Secure database during bootstrap by removing anonymous users
-- and setting a password
USE mysql;
DELETE FROM `db`;
DELETE FROM `user` WHERE User = '';
UPDATE `user` SET PASSWORD = PASSWORD('{{password|escape}}') WHERE User = 'root';
