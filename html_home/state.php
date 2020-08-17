<?php
$name = $_POST['name'];
$value = $_POST['value'];

$servername = 'beetle-back.local';
$username = 'beetle';
$password = file_get_contents('/home/pi/beetle_db_passwd.txt');
$dbname = 'beetle';

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die('Connection failed: ' . $conn->connect_error);
}

$sql = 'UPDATE state SET ts = CURRENT_TIMESTAMP, value = "'.$value.'" WHERE name = "'.$name.'";';
$conn->query($sql);
$conn->close();
?>
