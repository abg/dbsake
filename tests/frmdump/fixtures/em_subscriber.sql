CREATE TABLE `em_subscriber` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `cdate` datetime DEFAULT NULL,
  `email` varchar(250) NOT NULL DEFAULT '',
  `bounced_hard` int(10) NOT NULL DEFAULT '0',
  `bounced_soft` int(10) NOT NULL DEFAULT '0',
  `bounced_date` date DEFAULT NULL,
  `ip` int(10) unsigned NOT NULL DEFAULT '0',
  `ua` text,
  `hash` varchar(32) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `email` (`email`),
  KEY `cdate` (`cdate`),
  KEY `hash` (`hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
