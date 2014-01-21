from setuptools import setup, find_packages
from os import path
import imp

base = path.dirname(__file__)

f = open(path.join(base, 'README.rst'))
long_description = f.read().strip()
f.close()

f = open(path.join(base, 'requirements.txt'))
install_requires = [ r.strip() for r in f.readlines() if '#egg=' not in r ]
f.close()

f = open(path.join(base, 'ddcheck', 'version.py'))
version = imp.new_module('version')
exec(f.read(), version.__dict__)
f.close()

setup(
    name='ddcheck',
    version=version.__versionstr__,
    description='Check URLs and manage the respective records in DynDNS.',
    long_description=long_description,
    license='BSD',
    author='Jiri Barton',
    author_email='jbar@tele3.cz',
    url='https://github.com/whiskybar/ddcheck',
    packages=find_packages(exclude=('test_ddcheck',)),
    entry_points={'console_scripts': ['ddcheck = ddcheck.console:main']},
    install_requires=install_requires,
    include_package_data=True,
    zip_safe=False,
    test_suite = 'nose.collector',
)

