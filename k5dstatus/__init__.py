from gi.repository import GLib
import sys
import os
import yaml
import asyncio
import argparse
from dbus.mainloop.glib import DBusGMainLoop
from .service import BlockManager
from .barproto import BarManager, InputParser
from .procman import run_from_config
try:
    import gpotato
except ImportError:
    pass

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--config', '-c', default='~/.k5dstatus.conf',
                   help='Config file to load')


def start():
    """
    Orchestrates the start of everything, injects dependencies, sets up event
    loops, and all the other things that need to happen
    """
    # Remap some stuff so we don't corrupt pipes
    i3bar_blocks, sys.stdout = sys.stdout, sys.stderr
    i3bar_input, sys.stdin = sys.stdin, None

    args = parser.parse_args()

    DBusGMainLoop(set_as_default=True)
    #asyncio.set_event_loop_policy(gbulb.GLibEventLoopPolicy())

    try:
        with open(os.path.expanduser(args.config)) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}

    manager = BlockManager(config)

    blockman = BarManager(i3bar_blocks, manager, config)
    iparse = InputParser(i3bar_input, manager, config)

    GLib.idle_add(run_from_config, config, sys.argv[1:])
    # FIXME: Feed blockman, iparse coroutines to event loop

    main = GLib.MainLoop()
    main.run()
    # Do this instead when gbulb is better
    #asyncio.get_event_loop().run_forever()
