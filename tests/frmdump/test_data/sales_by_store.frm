TYPE=VIEW
query=select concat(`c`.`city`,_utf8\',\',`cy`.`country`) AS `store`,concat(`m`.`first_name`,_utf8\' \',`m`.`last_name`) AS `manager`,sum(`p`.`amount`) AS `total_sales` from (((((((`sakila`.`payment` `p` join `sakila`.`rental` `r` on((`p`.`rental_id` = `r`.`rental_id`))) join `sakila`.`inventory` `i` on((`r`.`inventory_id` = `i`.`inventory_id`))) join `sakila`.`store` `s` on((`i`.`store_id` = `s`.`store_id`))) join `sakila`.`address` `a` on((`s`.`address_id` = `a`.`address_id`))) join `sakila`.`city` `c` on((`a`.`city_id` = `c`.`city_id`))) join `sakila`.`country` `cy` on((`c`.`country_id` = `cy`.`country_id`))) join `sakila`.`staff` `m` on((`s`.`manager_staff_id` = `m`.`staff_id`))) group by `s`.`store_id` order by `cy`.`country`,`c`.`city`
md5=29ea3504bd7a05e13be21a77c718ee38
updatable=0
algorithm=0
definer_user=root
definer_host=localhost
suid=2
with_check_option=0
timestamp=2014-07-11 16:47:58
create-version=1
source=SELECT\nCONCAT(c.city, _utf8\',\', cy.country) AS store\n, CONCAT(m.first_name, _utf8\' \', m.last_name) AS manager\n, SUM(p.amount) AS total_sales\nFROM payment AS p\nINNER JOIN rental AS r ON p.rental_id = r.rental_id\nINNER JOIN inventory AS i ON r.inventory_id = i.inventory_id\nINNER JOIN store AS s ON i.store_id = s.store_id\nINNER JOIN address AS a ON s.address_id = a.address_id\nINNER JOIN city AS c ON a.city_id = c.city_id\nINNER JOIN country AS cy ON c.country_id = cy.country_id\nINNER JOIN staff AS m ON s.manager_staff_id = m.staff_id\nGROUP BY s.store_id\nORDER BY cy.country, c.city
client_cs_name=utf8
connection_cl_name=utf8_general_ci
view_body_utf8=select concat(`c`.`city`,\',\',`cy`.`country`) AS `store`,concat(`m`.`first_name`,\' \',`m`.`last_name`) AS `manager`,sum(`p`.`amount`) AS `total_sales` from (((((((`sakila`.`payment` `p` join `sakila`.`rental` `r` on((`p`.`rental_id` = `r`.`rental_id`))) join `sakila`.`inventory` `i` on((`r`.`inventory_id` = `i`.`inventory_id`))) join `sakila`.`store` `s` on((`i`.`store_id` = `s`.`store_id`))) join `sakila`.`address` `a` on((`s`.`address_id` = `a`.`address_id`))) join `sakila`.`city` `c` on((`a`.`city_id` = `c`.`city_id`))) join `sakila`.`country` `cy` on((`c`.`country_id` = `cy`.`country_id`))) join `sakila`.`staff` `m` on((`s`.`manager_staff_id` = `m`.`staff_id`))) group by `s`.`store_id` order by `cy`.`country`,`c`.`city`
