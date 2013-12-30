![dbsake](https://raw.github.com/abg/dbsake/master/sake-icon.png)
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
