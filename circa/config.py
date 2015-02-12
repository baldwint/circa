import os
from ConfigParser import ConfigParser

def load_default_config():
    config = ConfigParser()
    config.add_section('galvos')
    config.set('galvos', 'xgalvo',  'Dev2/ao0')
    config.set('galvos', 'ygalvo',  'Dev2/ao1')
    config.add_section('counting')
    config.set('counting', 'pulsechan',  'Dev1/ctr1')
    config.set('counting', 'countchan',  'Dev1/ctr0')
    return config

def load_config(path=None):
    config = load_default_config()
    if path is None:
        path = os.path.join(os.path.expanduser('~'), 'circa.cfg')
    config.read(path)
    return config
