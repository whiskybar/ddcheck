import os.path
from setuptools import setup, find_packages

VERSION = (0, 0, 1)
__version__ = VERSION
__versionstr__ = '.'.join(map(str, VERSION))

ROOT = os.path.dirname(__file__)
requirements = [line.strip() for line in open(os.path.join(ROOT, 'requirements.txt'))]

setup(
    name = 'ddcheck',
    version = __versionstr__,
    description = 'Check URLs and manage the respective records in DynDNS.',
    long_description = '\n'.join((
        'ddcheck',
        '',
        'Check URLs and manage the respective records in DynDNS.',
    )),
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
    ] + requirements,
    test_suite = 'nose.collector',
)

