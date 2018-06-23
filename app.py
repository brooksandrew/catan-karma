"""
Run the application


Make POST request to test:
```
curl -H 'Content-Type: application/json' -X POST -d '{"foo":"more_foo"}' http://127.0.0.1:5000/catan-spectator/instruction_text -v
```

"""

import subprocess
import os, time, sys, json
import re
import requests
from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread
from queue import Queue, Empty
from parse import parse

from utils import Player, Rolls, Game, roll_dice, check_simulated_quantiles

# --------------------------------
# Templates
# --------------------------------

template_addplayer = "b'name:{name} color:{color}, seat:{seat}"
template_addsettlement = "b'{color} buys settlement, builds at ({coord}){:.}"
template_moverobber = "b'{color} moves robber to {tile_id},{:.}"
template_roll = "b'{color} rolls {roll}{:.}'"


def match_template(x):
    templates = {
        'add_player': template_addplayer,
        'add_settlement': template_addsettlement,
        'move_robber': template_moverobber,
        'roll': template_roll
    }
    for k, template in templates.items():
        result = parse(template, x)
        if result:
            return k, result.named



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

    a = request.get_json()
    g = Game()
    rolls = Rolls()

    print('loggy', file=sys.stderr)
    print(a)
    print('endloggy')
    print(g.players)

    app.logger.debug("JSON received...")
    app.logger.debug(request.get_json())

    if request.method in ['PUT', 'POST']:
        things.append(a)
        print(a)
        matched_instruction = match_template(a)
        print(matched_instruction)

        if matched_instruction is 'add_settlement':
            print('ok')

        return 'Added instruction: {}'.format(a)
    else:
        return str(things)


@app.route('/stats', methods=['GET'])
def stats1():
    # TODO: calculate stats from game state
    print('STATS')
    return jsonify({'stats': 'mystats'})


if __name__ == '__main__':

    # simrolls = Rolls()

    #
    # gsim.players['simp1'].add_settlements([5, 3, 11])
    # gsim.players['simp1'].add_settlements([5, 3, 11])
    # gsim.players['simp1'].add_settlements([5, 3, 11])


    # settlements don't stick in UI when shell=False
    p = subprocess.Popen(['catan-spectator', '--use_stdout'], stdout=subprocess.PIPE, shell=False)
    nbsr = NonBlockingStreamReader(p.stdout)

    b = Thread(name='catan_spectator_listener', target=catan_spectator_listener, kwargs={'stream_reader': nbsr})
    b.start()

    app.run(debug=None)

