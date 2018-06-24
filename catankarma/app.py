"""
Run the application


Make POST request to test:
```
curl -H 'Content-Type: application/json' -X POST -d '{"foo":"more_foo"}' http://127.0.0.1:5000/catan-spectator/instruction_text -v
```

"""

import subprocess
import sys
from collections import defaultdict
from queue import Queue, Empty
from threading import Thread

import hexgrid
import requests
from flask import Flask, jsonify, request
from parse import parse

from catankarma.utils import Player, Rolls, Game

# --------------------------------
# Templates
# --------------------------------

template_addplayer = "b'name: {name} color: {color}, seat: {seat}"
template_addsettlement = "b'{color} buys settlement, builds at {coord}"
template_addcity = "b'{color} buys city, builds at {coord}"
template_moverobber = "b'{color} moves robber to {tile_id},{:.}"
template_roll = "b'{color} rolls {roll}"
template_board_setup = "b'numbers: {numbers}"


def match_template(x):
    """Parse string from catan-log to a structured instruction"""
    x = x[:-3] if x[-3:] == "\\n'" else x
    templates = {
        'add_player': template_addplayer,
        'add_settlement': template_addsettlement,
        'add_city': template_addcity,
        'move_robber': template_moverobber,
        'roll': template_roll,
        'board_setup': template_board_setup
    }
    for k, template in templates.items():
        result = parse(template, x)
        if result:
            return k, result.named
    return None, None


def tiles_touching_node(node):
    """
    Get tile IDs touching a node coord, node is type str.
    Ex:
    >>> tiles_touching_node('(2 SW)')
    >>> [2, 3]
    """

    # Get node coord from the node string representation
    map_node_fmt2coord = {hexgrid.location(hexgrid.NODE, n_coord): n_coord for n_coord in hexgrid.legal_node_coords()}
    node_coord = map_node_fmt2coord[node]

    # map node to tile coordinates
    map_node2tile = defaultdict(list)
    for t in hexgrid.legal_tile_ids():
        nodes = hexgrid.nodes_touching_tile(t)
        for n in nodes:
            map_node2tile[n].append(t)

    return map_node2tile[node_coord]


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
            # print('now!!!', datetime.now(), output)
            # headers = {"content-type": "application/json"}
            requests.put(url='http://localhost:5000/catan-spectator/instruction_text', json=str(output))


# -----------------------------------
# FLASK APP (stub)
# -----------------------------------

app = Flask(__name__)


# initialize game state
things = []
g = Game()
rolls = Rolls()


@app.route('/catan-spectator/instruction_text', methods=['GET', 'POST', 'PUT'])
def process_catan_spectator_instruction():

    a = request.get_json()
    print('loggy', file=sys.stderr)
    print(a)
    print('endloggy')

    app.logger.debug("JSON received...")
    app.logger.debug(request.get_json())

    if request.method in ['PUT', 'POST']:
        things.append(a)
        instruct_type, instruct_cmd = match_template(a)
        if instruct_type in ['add_settlement', 'add_city']:
            tile_ids = tiles_touching_node(instruct_cmd['coord'])
            tile_die_numbers = [int(g.tile_numbers[t-1]) for t in tile_ids if g.tile_numbers[t-1] != 'None']
            print('adding settlements')
            print(tile_die_numbers)
            g.players[instruct_cmd['color']].add_settlements(tile_die_numbers)  # make these ints
        elif instruct_type == 'move_robber':
            pass  # TODO
        elif instruct_type == 'add_player':
            g.add_players({instruct_cmd['color']: Player(rolls)})
        elif instruct_type == 'roll':
            g.add_roll(instruct_cmd['roll'])
        elif instruct_type == 'board_setup':
            g.tile_numbers = instruct_cmd['numbers'].split()  # TODO: formalize this method?
        return 'Added instruction: {}'.format(a)
    else:
        return str(things)


@app.route('/stats/resources_collected', methods=['GET'])
def stats_resource_collected():
    player_color = request.args.get('player')
    if player_color:
        return jsonify({player_color: g.players[player_color].resources_count()})
    else:
        return jsonify({p: g.players[p].resources_count() for p in g.players})  # TODO: not updating from 0


@app.route('/stats/resources_expected', methods=['GET'])
def stats_resources_expected():
    player_color = request.args.get('player')
    if player_color:
        return jsonify({player_color: g.players[player_color].expected_resources_count()})
    else:
        return jsonify({p: g.players[p].expected_resources_count() for p in g.players})


@app.route('/stats', methods=['GET'])
def stats_percentile():
    player_color = request.args.get('player')
    if player_color:
        return jsonify({player_color: g.players[player_color].get_percentile_from_resources_exact()})
    else:
        return jsonify({p: g.players[p].get_percentile_from_resources_exact() for p in g.players})


@app.route('/game/players', methods=['GET'])
def game_players():
    """Not essential to stats, but exposes the players endpoint.  Useful for testing"""
    return jsonify({'players': list(g.players.keys())})


@app.route('/game/player_attributes', methods=['GET'])
def game_player_attrs():
    """Not essential to stats, but exposes the players endpoint.  Useful for testing"""
    player_color = request.args.get('player')
    attr = request.args.get('attr')
    return jsonify({player_color: getattr(g.players[player_color], attr)})


@app.route('/game/settlements', methods=['GET'])
def game_player_settlements():
    """Not essential to stats, but exposes the players endpoint.  Useful for testing"""
    player_color = request.args.get('player')
    return jsonify({'settlements': g.players[player_color].settlements})


@app.route('/game/rolls', methods=['GET'])
def game_rolls():
    """Not essential to stats, but exposes the players endpoint.  Useful for testing"""
    return jsonify({'rolls': rolls.get_roll_history()})


def main():

    p = subprocess.Popen(['catan-spectator', '--use_stdout'], stdout=subprocess.PIPE, shell=False)
    nbsr = NonBlockingStreamReader(p.stdout)

    b = Thread(name='catan_spectator_listener', target=catan_spectator_listener, kwargs={'stream_reader': nbsr})
    b.start()

    app.run(debug=None)


if __name__ == '__main__':
    main()



