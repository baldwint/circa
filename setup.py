from setuptools import setup

# dependencies
reqs = ['numpy', 'PyDAQmx', 'matplotlib', 'pyvisa']
# we also need wxPython, but pip cannot install this
extras = {}

# http://stackoverflow.com/a/7071358/735926
import re
VERSIONFILE = 'circa/__init__.py'
verstrline = open(VERSIONFILE, 'rt').read()
VSRE = r'^__version__\s+=\s+[\'"]([^\'"]+)[\'"]'
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % VERSIONFILE)

with open('README.rst') as f:
    readme = f.read()

setup(name='circa',
      version=verstr,
      description='A GUI for Wang lab confocal microscopes.',
      long_description=readme,
      url='https://github.com/baldwint/circa',
      author='Tom Baldwin',
      author_email='tbaldwin@uoregon.edu',
      license='MIT',
      classifiers=(
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering :: Visualization',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
      ),
      install_requires=reqs,
      extras_require=extras,
      packages=['circa', ],
      entry_points = {
          'console_scripts': ['circa=circa.acquisition:main'],
      },
      )
