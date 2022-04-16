#!/usr/bin/env python3

'''
TODO: consider using Flask-BasicAuth
https://flask-basicauth.readthedocs.io/en/latest/
'''

import flask
import json
import logging
import os

persistent_state_file = '/var/www/html/beetle/state.json'
state = {}

api = flask.Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@api.route('/state', methods=['GET', 'POST'])
def state():
    global persistent_state_file
    global state

    if flask.request.method == 'GET':
        return flask.jsonify(state)
    elif flask.request.method == 'POST':
        state = flask.request.get_json()
        with open(persistent_state_file, 'w+') as fout:
            fout.write(json.dumps(state, indent=4))
            fout.flush()
            os.fsync(fout.fileno())
        return 'success', 200
    else:
        return 'fail', 400

if __name__ == '__main__':

    # initialize from persistent store of state
    try:
        with open(persistent_state_file) as fin:
            state = json.loads(fin.read())
    except FileNotFoundError:
        print('%s not found' % persistent_state_file)

    # run flask
    api.run(host='0.0.0.0')
