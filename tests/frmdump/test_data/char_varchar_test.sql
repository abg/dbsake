CREATE TABLE `char_varchar_test` (
  `a` varchar(64) DEFAULT 'foo bar baz',
  `b` char(64) DEFAULT 'biz boz buz',
  `c` varchar(9000) DEFAULT 'foo'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
