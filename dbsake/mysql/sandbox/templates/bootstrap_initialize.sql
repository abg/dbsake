-- don't write any bootstrap stuff to the binary log
-- even if it is enabled
SET @@session.sql_log_bin = 0;
CREATE DATABASE IF NOT EXISTS `mysql`;
USE mysql;


