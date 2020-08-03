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

        </script>
    </head>

<body onload='init()' style='font-family:arial;font-weight:normal;color:silver;background-color:black;zoom:500%;'>

<h2>Speed</h2>
<h1 class='updateme' txtfile='hspeed.txt'></h1>
<h2>Speed (filtered)</h2>
<h1 class='updateme' txtfile='fspeed.txt'></h1>

</body>
</html>
