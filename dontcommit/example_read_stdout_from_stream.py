"""
Example of how to read from std out of a subprocess
In this example, output does not happen until the subprocess is complete, which is not ideal.

Output:
    2018-06-09 18:46:27.349787 b'fast\n'
    2018-06-09 18:46:27.350098 b'fast still\n'
    2018-06-09 18:46:27.350143 b'back after 1 seconds\n'
    2018-06-09 18:46:27.350174 b'back again after 2 seconds\n'
    2018-06-09 18:46:27.350200 b'boom\n'
    2018-06-09 18:46:27.350223 b'boom\n'
    2018-06-09 18:46:27.350245 b'boom\n'
    2018-06-09 18:46:27.357803 that is all

"""
import subprocess
import os
import time
import requests
from datetime import datetime
from flask import Flask, jsonify
from threading import Thread
from queue import Queue, Empty


# p = subprocess.Popen(['python', '/Users/ajb/Downloads/catan_spectator/catan_spectator/main.py'], stdout=subprocess.PIPE, shell=False)
# p = subprocess.Popen(['python', '-u', 'shell.py'], stdout=subprocess.PIPE, shell=False)  # need "-u" for sleep to work


class NonBlockingStreamReader:
    """from http://eyalarubas.com/python-subproc-nonblock.html"""

    def __init__(self, stream):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            while True:
                line = stream.readline()
                # print(str(line), 'hah')
                if line:
                    queue.put(line)
                else:
                    raise UnexpectedEndOfStream


        self._t = Thread(target = _populateQueue,
                args = (self._s, self._q))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout = None):
        try:
            return self._q.get(block = timeout is not None,
                    timeout = timeout)
        except Empty:
            return None


class UnexpectedEndOfStream(Exception): pass


import fcntl

def non_block_read(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.readline()
    except:
        return ""


def catan_spectator_listener(stream_reader):
    while True:
        # time.sleep(0.5)
        # output = p.stdout.readline()  # blocking
        # output = non_block_read(p.stdout)
        output = stream_reader.readline(0.1)
        if not output:
            pass
        else:
            print(datetime.now(), output)
            print('lookie-begin')
            print(output)
            print('lookie-end')
        requests.put('http://localhost:5000/api/catan-spectator/instruction_text', json=jsonify({'ok':output}))


# -----------------------------------
# FLASK APP (stub)
# -----------------------------------

app = Flask(__name__)


@app.route('/catan-spectator/instruction_text', methods=['PUT', 'GET'])
def process_catan_spectator_instruction():
    # TODO: modify game state:  add_settlement, roll
    #return '1'
    pass


@app.route('/stats', methods=['GET'])
def stats1():
    # TODO: calculate stats from game state
    return 1



if __name__ == '__main__':
    p = subprocess.Popen(['catan-spectator', '--use_stdout'], stdout=subprocess.PIPE, shell=False)
    nbsr = NonBlockingStreamReader(p.stdout)

    b = Thread(name='catan_spectator_listener', target=catan_spectator_listener, kwargs={'stream_reader': nbsr})
    app.run(debug=True)