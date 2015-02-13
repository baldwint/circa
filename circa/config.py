import os
from ConfigParser import ConfigParser

def load_default_config():
     # The default configuration below is set up for my (tkb)
     # room-temperature setup in room 273. To use a different setup,
     # don't modify this source code - it is better to make a
     # ``circa.cfg`` file in your home directory. The settings defined
     # there will override these.
     # See the file ``circa_example.cfg`` for a file that makes circa
     # work on Andrew's cryogenic setup in room 272.
    config = ConfigParser()
    config.add_section('galvos')
    config.set('galvos', 'xgalvo',  'Dev2/ao0')
    config.set('galvos', 'ygalvo',  'Dev2/ao1')
    config.add_section('counting')
    config.set('counting', 'pulsechan',  'Dev1/ctr1')
    config.set('counting', 'countchan',  'Dev1/ctr0')
    config.add_section('fast')
    config.set('fast', 'pulsechan',  'Dev1/ctr2')
    config.set('fast', 'countchan',  'Dev1/ctr0')
    config.set('fast', 'sampleclk',  'PFI34')
    config.set('fast', 'det_afg',  'GPIB::11')
    config.set('fast', 'rf_afg',  'GPIB::10')
    return config

def load_config(path=None):
    config = load_default_config()
    if path is None:
        path = os.path.join(os.path.expanduser('~'), 'circa.cfg')
    config.read(path)
    return config
