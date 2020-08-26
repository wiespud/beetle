<!DOCTYPE html>

<html>
    <script src='jquery-3.5.1.min.js'></script>
    <head>
        <meta http-equiv='Content-Type' content='text/html; charset=utf8' />
        <script type='text/javascript'>

            function update(state) {
                var elems = document.getElementsByClassName('updateme');
                var date = new Date();
                var now = date.getTime();
                for (var i = 0; i < elems.length; i++) {
                    var elem = elems[i];
                    elem.innerText = state[elem.id]['value'];
                    var ts = Date.parse(state[elem.id]['ts']);
                    var timeout = 1000.0 * parseFloat(state[elem.id]['timeout']);
                    if (timeout > 0.0) {
                        if (now > ts + timeout) {
                            elem.style.color = 'red';
                        } else {
                            elem.style.color = 'silver';
                        }
                    }
                }
            }

            function refresh() {
                var req = new XMLHttpRequest();
                req.onreadystatechange = function () {
                    if (req.readyState == 4 && req.status == 200) {
                        var state = JSON.parse(req.responseText);
                        update(state);
                    }
                }
                req.open('GET', 'state.json', true);
                req.setRequestHeader('Cache-Control', 'no-cache');
                req.send(null);
            }

            function init() {
                refresh();
                var int = self.setInterval(function () {
                    refresh();
                }, 500);
            }

            function button(elem) {
                var update_elem = document.getElementById(elem.className);
                var value = elem.getAttribute('value');
                update_elem.innerText = value;
                $.ajax({
                    url: 'state.php',
                    type: 'post',
                    data: { 'name': elem.className, 'value': value }
                });
            }

        </script>
    </head>

    <body onload='init()' style='font-family:arial;font-weight:bold;color:silver;background-color:black;zoom:400%;'>

        <div style='font-size:2.5em;'><a class='updateme' id='v'></a> V</div>
        <div style='font-size:2.5em;'><a class='updateme' id='v_acc_batt'></a> V</div>
        <div style='font-size:2.5em;'><a class='updateme' id='v_i_sense'></a> V</div>
        <div><a class='updateme' id='v_min'></a> V&nbsp;&nbsp;&nbsp;&nbsp;<a class='updateme' id='v_av'></a> V&nbsp;&nbsp;&nbsp;&nbsp;<a class='updateme' id='v_max'></a> V</div>
        <div style='margin-bottom:10px;'>Front: <a class='updateme' id='front_t_av'></a> C&nbsp;&nbsp;&nbsp;&nbsp;Back: <a class='updateme' id='back_t_av'></a> C</div>

        <div>Trip Odometer <button class='trip_odometer' value='0.0' onclick='button(this)' style='background-color:silver'>Reset</button></div>
        <div style='font-size:2.5em;margin-bottom:10px;'><a class='updateme' id='trip_odometer'></a> mi</div>

        <div>Charge Odometer</div>
        <div style='font-size:2.5em;margin-bottom:10px;'><a class='updateme' id='charge_odometer'></a> mi</div>

        <div style='margin-bottom:2px;'>Charger: <a class='updateme' id='charger'></a></div>
        <div>
            <button class='charger' value='enabled' onclick='button(this)' style='background-color:silver'>Enable</button>
            <button class='charger' value='disabled' onclick='button(this)' style='background-color:silver'>Disable</button>
            <button class='charger' value='once' onclick='button(this)' style='background-color:silver'>Once</button>
        </div>

    </body>
</html>
