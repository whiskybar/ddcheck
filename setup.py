from os import path
from setuptools import setup, find_packages

VERSION = (0, 0, 1)
__version__ = VERSION
__versionstr__ = '.'.join(map(str, VERSION))

base = path.dirname(__file__)

f = open(path.join(base, 'README.rst'))
long_description = f.read().strip()
f.close()

f = open(path.join(base, 'requirements.txt'))
install_requires = [ r.strip() for r in f.readlines() if '#egg=' not in r ]
f.close()

setup(
    name = 'ddcheck',
    version = __versionstr__,
    description = 'Check URLs and manage the respective records in DynDNS.',
    long_description = long_description,
    license = 'BSD',

    packages = find_packages(
        where = '.',
        exclude = ('test_ddcheck', )
    ),
    entry_points = {
        'console_scripts': [
            'ddcheck = ddcheck.server:main',
        ],
    },

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires = [
        'setuptools>=0.6b1',
    ] + install_requires,
    test_suite = 'nose.collector',
)

