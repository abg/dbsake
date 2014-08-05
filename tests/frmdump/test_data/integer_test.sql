CREATE TABLE `integer_test` (
  `id` bigint(8) unsigned zerofill DEFAULT NULL,
  `val0` smallint(6) DEFAULT '-32',
  `val1` smallint(5) unsigned DEFAULT '16385',
  `val2` mediumint(9) DEFAULT '-65792',
  `val3` mediumint(8) unsigned DEFAULT '65792'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
