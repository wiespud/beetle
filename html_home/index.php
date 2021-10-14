<!DOCTYPE html>

<html>
    <script src='jquery-3.5.1.min.js'></script>
    <head>
        <meta http-equiv='Content-Type' content='text/html; charset=utf8' />
        <script type='text/javascript'>

            function update(state) {
                // handle updateme class elements
                var elems = document.getElementsByClassName('updateme');
                var date = new Date();
                var now = date.getTime();
                for (var i = 0; i < elems.length; i++) {
                    var elem = elems[i];
                    elem.innerText = state[elem.id]['value'];
                    var ts = Date.parse(state[elem.id]['ts']);
                    var timeout = 1000.0 * parseFloat(state[elem.id]['timeout']);
                    if (timeout > 0.0) {
                        // Don't use timeout from json since it is only updated
                        // every 5 minutes. Use a 10 minute timeout instead.
                        if (now > ts + 600000.0) {
                            elem.style.color = 'red';
                        } else {
                            elem.style.color = 'silver';
                        }
                    }
                }

                // handle leds
                var elems = document.getElementsByClassName('led');
                for (var i = 0; i < elems.length; i++) {
                    var elem = elems[i];
                    var ts = Date.parse(state[elem.id]['ts']);
                    var timeout = 1000.0 * parseFloat(state[elem.id]['timeout']);
                    // Don't use timeout from json since it is only updated
                    // every 5 minutes. Use a 10 minute timeout instead.
                    if (timeout > 0.0 && now > ts + 600000.0) {
                        elem.style.backgroundColor = 'red';
                    } else if (state[elem.id]['value'] == 'enabled' ||
                               state[elem.id]['value'] == '1') {
                        elem.style.backgroundColor = 'green';
                    } else {
                        elem.style.backgroundColor = 'grey';
                    }
                }

                // handle location url
                var locElem = document.getElementById('location');
                var url = 'https://www.google.com/maps/search/?api=1&query=';
                url += state['lat']['value'];
                url += ',';
                url += state['lon']['value'];
                locElem.setAttribute('href', url);
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
                }, 5000);
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

        <div style='position:absolute;top:10px;right:10px;'>
            AC <span class='led' id='ac_present' style='height:12px;width:12px;background-color:green;border-radius:50%;display:inline-block;'></span>
        </div>
        <div style='position:absolute;top:30px;right:10px;'>
            Charger <span class='led' id='charging' style='height:12px;width:12px;background-color:green;border-radius:50%;display:inline-block;'></span>
        </div>
        <div style='position:absolute;top:50px;right:10px;'>
            DCDC <span class='led' id='dcdc' style='height:12px;width:12px;background-color:green;border-radius:50%;display:inline-block;'></span>
        </div>
        <div style='position:absolute;top:70px;right:10px;'>
            Fan <span class='led' id='controller_fan' style='height:12px;width:12px;background-color:green;border-radius:50%;display:inline-block;'></span>
        </div>

        <a id='location' href='https://www.google.com/maps/' style='position:absolute;top:600px;right:32px;zoom:16%;'><img src='maps.ico'/></a>
        <div class='updateme' id='ip' style='position:absolute;top:225px;right:18px;zoom:60%;'>00.00</div>

        <div style='font-size:2.5em;'><a class='updateme' id='v'></a> V</div>
        <div style='font-size:2.5em;'><a class='updateme' id='v_acc_batt'></a> V</div>
        <div>Min: <a class='updateme' id='v_min'></a> V&nbsp;&nbsp;&nbsp;&nbsp;Max: <a class='updateme' id='v_max'></a> V</div>
        <div>Front: <a class='updateme' id='front_t_av'></a> C&nbsp;&nbsp;&nbsp;&nbsp;Back: <a class='updateme' id='back_t_av'></a> C</div>
        <div style='margin-bottom:10px;'>Controller: <a class='updateme' id='controller_temp'></a> C</div>

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
