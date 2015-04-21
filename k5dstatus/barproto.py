"""
Deals with the interface to i3bar.
"""
import asyncio
# import ijson
import signal
import json
import subprocess
import re

# TODO http://i3wm.org/docs/i3bar-protocol.html

STOP_SIGNAL = signal.SIGUSR1
CONT_SIGNAL = signal.SIGUSR2

# Make sure to register stop_signal and cont_signal as to not lock-up the whole
# process (which could fuck with d-bus) but instead just stop output to i3bar.

# Make sure to register for click events and handle them.

VERSION_RE = re.compile(r'\d+(?:\.\d+)+')


def barversion():
    """barversion_hex() -> tuple(int)
    Get the version of i3bar as a tuple, eg (4, 10).
    """
    verstr = subprocess.check_output(['i3bar', '--version']).decode('utf-8')
    # i3bar version 4.8 (2014-06-15, branch "4.8") © 2010-2014 Axel Wagner and contributors\n'
    m = VERSION_RE.search(verstr)
    if m:
        ver = m.group(0)
        return tuple(map(int, ver.split('.')))


def stripxml(txt):
    "Strip Pango markup (aka XML document fragment)"
    import xml.etree.ElementTree as ET
    tree = ET.fromstring("<fragment>{}</fragment>".format(txt))
    return ET.tostring(tree, encoding='utf8', method='text').decode('utf-8')


def BarManager(stream, blocks, config):
    # FIXME: Make this a coroutine
    # FIXME: Use a streaming JSON writer?
    # Set signal handlers
    stream.write(json.dumps({
        "version": 1,
        "stop_signal": STOP_SIGNAL,
        "cont_signal": CONT_SIGNAL,
        "click_events": True
    }))
    stream.write('\n[')
    stream.flush()

    i3bver = barversion()

    def fixblock(block):
        print(block)
        if i3bver < (4, 10):
            # Pango Markup is unsupported; strip and hope for the best
            if 'markup' in block and block['markup'] == 'pango':
                del block['markup']
                block['full_text'] = stripxml(block['full_text'])
                if 'short_text' in block:
                    block['short_text'] = stripxml(block['short_text'])
        print(block)
        return block

    @blocks.blockchanged.handler
    @blocks.blockadded.handler
    @blocks.blockremoved.handler
    def writeout(*_):
        # FIXME: Implement flow control so that updates get lost rather than backed up
        stream.write(json.dumps([
            fixblock(block.json())
            for block in blocks
        ]))
        stream.write(',\n')
        stream.flush()

def InputParser(stream, blocks, config):
    return NotImplemented