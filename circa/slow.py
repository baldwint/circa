from time import sleep
import itertools
import numpy as n

def fake_scan(gen, t=0.1, **kwargs):
    for step in gen:
        sleep(t)
        yield int(200000 * n.random.random())

def gen_2D(X, Y, xgalvo, ygalvo):
    for y in Y:
        ygalvo.value = y
        for x in X:
            xgalvo.value = x
            yield

def repeat_gen(gen, *args, **kwargs):
    """ repeatedly instantiate gen and run it to completion. """
    while True:
        current = gen(*args, **kwargs)
        #yield from current
        for result in current:
            yield result

def chunk(gen, n=1):
    # not perfect unless n perfectly divides the lenght of gen
    while True:
        for i in xrange(n-1):
            next(gen)
        yield next(gen)

def yielding_fromiter(gen, result):
    """
    fills the ND array ``result`` with values from the ``gen`` iterator,
    yielding after each insertion so that you can do something else
    (like incremental plotting).

    """
    dimensions = [xrange(n) for n in result.shape]
    coords = itertools.product(*dimensions)
    coords = itertools.cycle(coords) # if gen keeps going, repeat
    for loc,val in itertools.izip(coords,gen):
        result[loc] = val
        yield

def make_generator_factory(xgalvo, ygalvo, pulsechan, countchan):
    """
    given two galvonometer objects (xgalvo, ygalvo) and strings
    identifying the counter pair used for counting (pulsechan,
    countchan), return a function that would produce data generators for
    2D scans using those parameters.
    """

    def make_data_generator(X, Y, t, vector, repeat=False):
        """
        Given the scan parameters (X, Y, t) and an array in which to
        put the results of the scan (vector), construct a generator
        that would perform the scan.
        """

        # scan generator
        try:
            from expt import scan
        except NotImplementedError:
            scan = fake_scan

        def datagen(X, Y, t):
            if repeat:
                gen = repeat_gen(gen_2D, X, Y, xgalvo, ygalvo)
            else:
                gen = gen_2D(X, Y, xgalvo, ygalvo)
            return scan(gen, t, pulsechan=pulsechan, countchan=countchan)

        gen = chunk(yielding_fromiter(datagen(X, Y, t), vector),
                n = vector.shape[-1])

        return gen

    return make_data_generator


