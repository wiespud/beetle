<!DOCTYPE html>

<html>
    <script src='jquery-3.5.1.min.js'></script>
    <head>
        <meta http-equiv='Content-Type' content='text/html; charset=utf8' />
        <script type='text/javascript'>

            function refresh() {
                var elems = document.getElementsByClassName('updateme');
                for (var i = 0; i < elems.length; i++) {
                    let req = new XMLHttpRequest();
                    let elem = elems[i];
                    let txtfile = elem.getAttribute('txtfile');
                    req.onreadystatechange = function () {
                        if (req.readyState == 4 && req.status == 200) {
                            elem.innerText = req.responseText;
                        }
                    }
                    req.open('GET', txtfile, true);
                    req.setRequestHeader('Cache-Control', 'no-cache');
                    req.send(null);
                }
            }

            function init() {
                refresh();
                var int = self.setInterval(function () {
                    refresh();
                }, 500);
            }

            function button(elem) {
                var update_elem = document.getElementById(elem.className);
                update_elem.innerText = elem.id;
                $.ajax({
                    url: 'state.php',
                    type: 'post',
                    data: { 'name': elem.className, 'value': elem.id }
                });
            }

        </script>
    </head>

<body onload='init()' style='font-family:arial;font-weight:normal;color:silver;background-color:black;zoom:500%;'>

<h2>Speed</h2>
<h1 class='updateme' txtfile='hspeed.txt'></h1>
<h2>Speed (filtered)</h2>
<h1 class='updateme' txtfile='fspeed.txt'></h1>
<br>

<h2>Charger: <a id='charger'><?php
$servername = '10.10.10.2';
$username = 'beetle';
$password = file_get_contents('/home/pi/db_passwd.txt');
$dbname = 'beetle';

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die('Connection failed: ' . $conn->connect_error);
}

$sql = 'SELECT * FROM state WHERE name = "charger";';
$result = $conn->query($sql);
$row = $result->fetch_assoc();
echo $row['value'];
$conn->close();
?></a></h2>
<button class='charger' id='enabled' onclick='button(this)' style='background-color:silver'>Enable</button>
<button class='charger' id='disabled' onclick='button(this)' style='background-color:silver'>Disable</button>

</body>
</html>
