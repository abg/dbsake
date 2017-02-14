CREATE TABLE `float_test` (
  `a` float DEFAULT '3.14159',
  `b` double DEFAULT '3.141592653589793',
  `c` float(4,3) unsigned zerofill DEFAULT '3.142',
  `d` double(13,12) unsigned DEFAULT '3.141592653590'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
