import os
import itertools

def get_next_filename(dir, fmt="file%03d", start=1):
    for i in itertools.count(start):
        if fmt % i not in os.listdir(dir):
            return fmt % i
