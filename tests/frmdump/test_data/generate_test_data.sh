#!/bin/bash

shopt -s extglob

# This script copies .frm from the system MySQL instance
# and generates the expected .sql data by running
# SHOW CREATE TABLE.  This is used to verify frmdump
# produces results identical to MySQL SHOW CREATE TABLE

DATADIR=${DATADIR:-/var/lib/mysql}

for name in ${DATADIR}/sakila/*.frm
do
    table=$(basename ${name} .frm)
    sql=$(mysql -sse "SHOW CREATE TABLE sakila.${table}" | cut -f2)
    # only strip foreign keys / auto_increment from base tables, not views
    if ! grep -Pq '^CREATE ALGORITHM=' <<< "${sql}"
    then
        # remove constraint lines
        sql=${sql//  CONSTRAINT*\\n/}
        # remove any lingering trailing commas before the final close paren
        sql=${sql/,\\n\)/\\n\)}
        sql=${sql/ AUTO_INCREMENT=+([0-9])/}
    else
        # minor adjustment to reduce minor differences for views vs frmdump
        sql=${sql/VIEW \`sakila\`./VIEW }
    fi
    echo -e "${sql};" > $(basename ${name} .frm).sql
    cp ${name} .
    chown ${SUDO_USER:-$(whoami)}: *.frm
done
