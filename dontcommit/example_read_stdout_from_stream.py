"""
Run the application
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
        time.sleep(0.5)
        output = stream_reader.readline()
        if not output:
            pass
        else:
            print('now!!!', datetime.now(), output)
            # requests.put('http://localhost:5000/catan-spectator/instruction_text', json=jsonify({'ok': output}))
            headers = {"content-type": "application/json"}
            requests.post('http://localhost:5000/catan-spectator/instruction_text', json.dumps({'ok': '1231235'}), headers)


# -----------------------------------
# FLASK APP (stub)
# -----------------------------------

app = Flask(__name__)


@app.route('/catan-spectator/instruction_text', methods=['GET', 'POST', 'PUT'])
def process_catan_spectator_instruction():
    # TODO: modify game state:  add_settlement, roll

    # if request.method in ['POST', 'PUT']:  #this block is only entered when the form is submitted
    #     return 'Submitted form.'

    print('loggy', file=sys.stderr)
    print(request.method)
    print(request.get_json())

    if request.method in ['PUT', 'POST']:
        return jsonify(request.get_json())
    else:
        headers = {"content-type": "application/json"}
        return jsonify(request.get_json())
        # return jsonify({'ok':'ok2'})


@app.route('/stats', methods=['GET'])
def stats1():
    # TODO: calculate stats from game state
    return jsonify({'stats': 'mystats'})


if __name__ == '__main__':

    # settlements don't stick in UI when shell=False
    p = subprocess.Popen(['catan-spectator', '--use_stdout'], stdout=subprocess.PIPE, shell=False)
    nbsr = NonBlockingStreamReader(p.stdout)

    b = Thread(name='catan_spectator_listener', target=catan_spectator_listener, kwargs={'stream_reader': nbsr})
    b.start()
    app.run(debug=True)

