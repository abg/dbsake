![dbsake](https://raw.github.com/abg/dbsake/master/sake-icon.png)

## DBSake

dbsake is a collection of tools to aid in administrating MySQL databases

Example:

```bash
# dbsake upgrade-mycnf --config /etc/my.cnf --target 5.6 --patch > my.56.upgrade.patch
```

This currently consists of two tools:

* ```split-mysqldump [--target|-t <mysql-version>] [--directory|-C <output-directory>] [--filter-command <cmd>] < input```

    Splits a mysqldump file into multiple separate files by table/views/routines/etc.

* ```upgrade-mycnf [--config path] [--target 5.1|5.5|5.6|5.7] [--patch]```

    Input a current my.cnf and output a my.cnf suitable for the target MySQL version

* ```frm-to-schema [path] [path...]```

  Decode a binary .frm file and output the CREATE TABLE statement.

* ```import-frm [source] [dest]```

  Convert a source .frm to an unpartitioned MyISAM table at dest.
  Note: This command does not yet generate an .MYI file so the resulting
        table must be fixed via "REPAIR TABLE ... USE_FRM" before it can be
        used by MySQL.

* ```filename-to-tablename [path] [path...]```

  convert path names from the MySQL filename encoding to unicode strings

* ```tablename-to-filename [path] [path...]```

  convert unicode names to MySQL filename encoded paths

* ```fincore [--verbose] [path] [path...]```

  Check for OS cached pages in a set of paths.

* ```uncache [--verbose] [path] [path...]```

  Drop cached pages in a set of paths.

* ```read-ib-binlog path```

  Read binary log filename and position from the InnoDB shared tablespace 
  system header page and format the information as a friendly CHANGE MASTER sql command.

## License

dbsake is licensed under GPLv2. 

dbsake includes a backport of argparse from python2.7, under the PSF license

dbsake includes python-baker, licensed under the ASF; See: https://bitbucket.org/mchaput/baker/wiki/Home 
