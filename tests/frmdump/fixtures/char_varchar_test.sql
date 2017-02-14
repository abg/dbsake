CREATE TABLE `char_varchar_test` (
  `a` varchar(64) DEFAULT 'foo bar baz',
  `b` char(64) DEFAULT 'biz boz buz',
  `c` varchar(9000) DEFAULT 'foo',
  UNIQUE KEY `ix_unique_b` (`b`) USING BTREE COMMENT 'unique index on `b` using BTREE algorithm',
  KEY `ix_foo` (`a`(32)) COMMENT 'example prefix index on column a'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
