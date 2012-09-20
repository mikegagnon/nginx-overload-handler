<?php

# idea from http://stackoverflow.com/questions/3892374/how-to-intentionally-create-a-long-running-mysql-query

$dbname = "my_wiki";
$query = "select benchmark(9999999999, md5('this will be hashed many times'));";
$env_user = getenv('MYSQL_USER');
if ($env_user != "") {
    $wgDBuser = $env_user;
} else {
    $wgDBuser = "root";
}

$db = mysql_connect("localhost", $wgDBuser, "dummyP@ssw0rd") or die("cant connect");
mysql_db_query($dbname, $query) or die(mysql_error());

?>

