import os
import itertools

def get_next_filename(dir, fmt="image%03d.npz", start=1):
    for i in itertools.count(start):
        if fmt % i not in os.listdir(dir):
            return fmt % i
