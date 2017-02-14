TYPE=VIEW
query=select `cu`.`customer_id` AS `ID`,concat(`cu`.`first_name`,_utf8\' \',`cu`.`last_name`) AS `name`,`a`.`address` AS `address`,`a`.`postal_code` AS `zip code`,`a`.`phone` AS `phone`,`sakila`.`city`.`city` AS `city`,`sakila`.`country`.`country` AS `country`,if(`cu`.`active`,_utf8\'active\',_utf8\'\') AS `notes`,`cu`.`store_id` AS `SID` from (((`sakila`.`customer` `cu` join `sakila`.`address` `a` on((`cu`.`address_id` = `a`.`address_id`))) join `sakila`.`city` on((`a`.`city_id` = `sakila`.`city`.`city_id`))) join `sakila`.`country` on((`sakila`.`city`.`country_id` = `sakila`.`country`.`country_id`)))
md5=f5f324e9ebe687efbbd4ad67651c1892
updatable=1
algorithm=0
definer_user=root
definer_host=localhost
suid=2
with_check_option=0
timestamp=2014-07-11 16:47:58
create-version=1
source=SELECT cu.customer_id AS ID, CONCAT(cu.first_name, _utf8\' \', cu.last_name) AS name, a.address AS address, a.postal_code AS `zip code`,\n	a.phone AS phone, city.city AS city, country.country AS country, IF(cu.active, _utf8\'active\',_utf8\'\') AS notes, cu.store_id AS SID\nFROM customer AS cu JOIN address AS a ON cu.address_id = a.address_id JOIN city ON a.city_id = city.city_id\n	JOIN country ON city.country_id = country.country_id
client_cs_name=utf8
connection_cl_name=utf8_general_ci
view_body_utf8=select `cu`.`customer_id` AS `ID`,concat(`cu`.`first_name`,\' \',`cu`.`last_name`) AS `name`,`a`.`address` AS `address`,`a`.`postal_code` AS `zip code`,`a`.`phone` AS `phone`,`sakila`.`city`.`city` AS `city`,`sakila`.`country`.`country` AS `country`,if(`cu`.`active`,\'active\',\'\') AS `notes`,`cu`.`store_id` AS `SID` from (((`sakila`.`customer` `cu` join `sakila`.`address` `a` on((`cu`.`address_id` = `a`.`address_id`))) join `sakila`.`city` on((`a`.`city_id` = `sakila`.`city`.`city_id`))) join `sakila`.`country` on((`sakila`.`city`.`country_id` = `sakila`.`country`.`country_id`)))
