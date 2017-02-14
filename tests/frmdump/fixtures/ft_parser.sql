CREATE TABLE `ft_parser` (
  `c` varchar(255) DEFAULT NULL,
  FULLTEXT KEY `c` (`c`) /*!50100 WITH PARSER `simple_parser` */ 
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
