'''
Interface to db state table used to share variables between front and back
'''

from datetime import datetime

EXPIRE_TIME = 60.0

class State:
    ''' State class '''
    def __init__(self, beetle):
        self.beetle = beetle

    def get(self, name):
        now = datetime.now()
        self.beetle.cur.execute('SELECT * FROM state WHERE name = "%s";' % name)
        row = self.beetle.cur.fetchall()[0]
        ts = row[1]
        value = row[3]
        timeout = row[4]
        last_update = (now - ts).total_seconds()
        if timeout > 0.0 and (last_update > 60.0 or last_update < 0.0):
            self.beetle.logger('state variable %s last update was %.01f '
                               'seconds ago' % (name, last_update))
            return None
        else:
            return value

    def set(self, name, value):
        self.beetle.cur.execute('UPDATE state SET ts = CURRENT_TIMESTAMP, '
                                'value = "%s" WHERE name = "%s";' % (value, name))
        self.db.commit()
