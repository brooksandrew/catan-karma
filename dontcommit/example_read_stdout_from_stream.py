"""
Run the application


Make POST request to test:
```
curl -H 'Content-Type: application/json' -X POST -d '{"foo":"more_foo"}' http://127.0.0.1:5000/catan-spectator/instruction_text -v
```

"""

import subprocess
import os, time, sys, json
import requests
from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread
from queue import Queue, Empty


class NonBlockingStreamReader:
    """from http://eyalarubas.com/python-subproc-nonblock.html"""

    def __init__(self, stream):
        """
        Args:
            stream: the stream to read from. Usually a process' stdout or stderr.
        """

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):
            """Collect lines from 'stream' and put them in 'queue'"""

            while True:
                line = stream.readline()
                # print(str(line), 'hah')
                if line:
                    queue.put(line)
                else:
                    raise UnexpectedEndOfStream

        self._t = Thread(target=_populateQueue, args=(self._s, self._q))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None


class UnexpectedEndOfStream(Exception):
    pass


def catan_spectator_listener(stream_reader):
    while True:
        # time.sleep(0.1)
        output = stream_reader.readline()
        if not output:
            pass
        else:
            print('now!!!', datetime.now(), output)
            headers = {"content-type": "application/json"}
            requests.put(url='http://localhost:5000/catan-spectator/instruction_text', json=str(output))
            # requests.put('http://localhost:5000/catan-spectator/instruction_text', json=jsonify({'ok': output}))
            # requests.put(url='http://localhost:5000/catan-spectator/instruction_text', json=json.dumps({'ok': '1231235'}))
            # requests.put(url='http://localhost:5000/catan-spectator/instruction_text', json='asd')


# -----------------------------------
# FLASK APP (stub)
# -----------------------------------

app = Flask(__name__)

things = []


@app.route('/catan-spectator/instruction_text', methods=['GET', 'POST', 'PUT'])
def process_catan_spectator_instruction():
    # TODO: modify game state:  add_settlement, roll

    # if request.method in ['POST', 'PUT']:  #this block is only entered when the form is submitted
    #     return 'Submitted form.'

    a = request.get_json()
    # print(request.method)
    print('loggy', file=sys.stderr)
    print(a)
    print('endloggy')

    app.logger.debug("JSON received...")
    app.logger.debug(request.get_json())

    if request.method in ['PUT', 'POST']:
        things.append(a)
        return 'Added instruction: {}'.format(a)
    else:
        # print(request.get_json)
        # return jsonify({'okssss':'ok2'})
        return str(things)


@app.route('/stats', methods=['GET'])
def stats1():
    # TODO: calculate stats from game state
    print('STATS')
    return jsonify({'stats': 'mystats'})


if __name__ == '__main__':

    # settlements don't stick in UI when shell=False
    p = subprocess.Popen(['catan-spectator', '--use_stdout'], stdout=subprocess.PIPE, shell=False)
    nbsr = NonBlockingStreamReader(p.stdout)

    b = Thread(name='catan_spectator_listener', target=catan_spectator_listener, kwargs={'stream_reader': nbsr})
    b.start()
    app.run(debug=True)

