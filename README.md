# catan-karma

catan-karma quantifies the luck factor in Settlers of Catan.  Specifically, it models the resource
collection cumulative density function for each player at each turn.  

A GUI is provided to track the rolls and builds which happen in real life (physical board).

## Usage

0. Install

```bash
git clone https://github.com/brooksandrew/catan-karma.git
cd catan-karma
pip install -e . --process-dependency-links
```

1. Run app

```bash
catan-karma
```

2. Track actions in the GUI.  Only rolls and builds (settlements or cities) are used.

3. Bask, taunt, whine or revel in the stats exposed in link_to_stats_page_when_it_is_finished.com

