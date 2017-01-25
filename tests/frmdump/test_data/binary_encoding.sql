CREATE TABLE `binary_encoding` (
  `a` binary(30) DEFAULT '12345\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0',
  `b` varbinary(30) DEFAULT '98765'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
