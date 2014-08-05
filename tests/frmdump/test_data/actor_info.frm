TYPE=VIEW
query=select `a`.`actor_id` AS `actor_id`,`a`.`first_name` AS `first_name`,`a`.`last_name` AS `last_name`,group_concat(distinct concat(`c`.`name`,\': \',(select group_concat(`f`.`title` order by `f`.`title` ASC separator \', \') from ((`sakila`.`film` `f` join `sakila`.`film_category` `fc` on((`f`.`film_id` = `fc`.`film_id`))) join `sakila`.`film_actor` `fa` on((`f`.`film_id` = `fa`.`film_id`))) where ((`fc`.`category_id` = `c`.`category_id`) and (`fa`.`actor_id` = `a`.`actor_id`)))) order by `c`.`name` ASC separator \'; \') AS `film_info` from (((`sakila`.`actor` `a` left join `sakila`.`film_actor` `fa` on((`a`.`actor_id` = `fa`.`actor_id`))) left join `sakila`.`film_category` `fc` on((`fa`.`film_id` = `fc`.`film_id`))) left join `sakila`.`category` `c` on((`fc`.`category_id` = `c`.`category_id`))) group by `a`.`actor_id`,`a`.`first_name`,`a`.`last_name`
md5=402b8673b0c61034644b5b286519d3f1
updatable=0
algorithm=0
definer_user=root
definer_host=localhost
suid=0
with_check_option=0
timestamp=2014-07-11 16:47:58
create-version=1
source=SELECT\na.actor_id,\na.first_name,\na.last_name,\nGROUP_CONCAT(DISTINCT CONCAT(c.name, \': \',\n		(SELECT GROUP_CONCAT(f.title ORDER BY f.title SEPARATOR \', \')\n                    FROM sakila.film f\n                    INNER JOIN sakila.film_category fc\n                      ON f.film_id = fc.film_id\n                    INNER JOIN sakila.film_actor fa\n                      ON f.film_id = fa.film_id\n                    WHERE fc.category_id = c.category_id\n                    AND fa.actor_id = a.actor_id\n                 )\n             )\n             ORDER BY c.name SEPARATOR \'; \')\nAS film_info\nFROM sakila.actor a\nLEFT JOIN sakila.film_actor fa\n  ON a.actor_id = fa.actor_id\nLEFT JOIN sakila.film_category fc\n  ON fa.film_id = fc.film_id\nLEFT JOIN sakila.category c\n  ON fc.category_id = c.category_id\nGROUP BY a.actor_id, a.first_name, a.last_name
client_cs_name=utf8
connection_cl_name=utf8_general_ci
view_body_utf8=select `a`.`actor_id` AS `actor_id`,`a`.`first_name` AS `first_name`,`a`.`last_name` AS `last_name`,group_concat(distinct concat(`c`.`name`,\': \',(select group_concat(`f`.`title` order by `f`.`title` ASC separator \', \') from ((`sakila`.`film` `f` join `sakila`.`film_category` `fc` on((`f`.`film_id` = `fc`.`film_id`))) join `sakila`.`film_actor` `fa` on((`f`.`film_id` = `fa`.`film_id`))) where ((`fc`.`category_id` = `c`.`category_id`) and (`fa`.`actor_id` = `a`.`actor_id`)))) order by `c`.`name` ASC separator \'; \') AS `film_info` from (((`sakila`.`actor` `a` left join `sakila`.`film_actor` `fa` on((`a`.`actor_id` = `fa`.`actor_id`))) left join `sakila`.`film_category` `fc` on((`fa`.`film_id` = `fc`.`film_id`))) left join `sakila`.`category` `c` on((`fc`.`category_id` = `c`.`category_id`))) group by `a`.`actor_id`,`a`.`first_name`,`a`.`last_name`
