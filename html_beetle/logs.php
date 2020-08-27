<?php
echo '<body style="font-family:arial;color:silver;background-color:black;">';
echo '<h1>Front</h1>';
$url='http://localhost/log.php';
$lines=file_get_contents($url);
echo '<div style="white-space: pre-wrap;">';
echo $lines;
echo '</div>';
echo '<h1>Back</h1>';
$url='http://10.10.10.2/log.php';
$lines=file_get_contents($url);
echo '<div style="white-space: pre-wrap;">';
echo $lines;
echo '</div>';
echo '</body>';
?>
