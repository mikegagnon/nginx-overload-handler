<?php

$dbname = "my_wiki";
$query = "select benchmark(9999999999, md5('this will be hashed many times'));";
$db = mysql_connect("localhost", getenv('MYSQL_USER'), "dummyP@ssw0rd") or die("cant connect");
mysql_db_query($dbname, $query) or die(mysql_error());

?>

