"""Python packaging stuff."""


from os.path import abspath, dirname, join, normpath
from subprocess import call

from setuptools import setup, find_packages, Command


class BaseCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class TestCommand(BaseCommand):

    description = "run self-tests"

    def run(self):
        ret = call(['py.test', '--quiet', '--cov-report=term-missing', '--cov', 'stormpath_config'])
        exit(ret)


setup(
    name = 'stormpath-config',
    version = '0.0.1',
    description = 'Official Stormpath library, used for loading the Stormpath configuration.',
    author = 'Stormpath, Inc.',
    author_email = 'support@stormpath.com',
    url = 'https://github.com/stormpath/stormpath-python-config',
    zip_safe = False,
    keywords = ['stormpath', 'configuration'],
    install_requires = [
        'flatdict>=1.2.0',
        'path.py==8.1.2',
        'pyjavaproperties==0.6',
        'pyyaml>=3.11',
    ],
    extras_require = {
        'test': ['codacy-coverage', 'mock', 'pytest', 'pytest-cov', 'python-coveralls', 'stormpath'],
    },
    packages = find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Security',
        'Topic :: Security :: Cryptography',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
    ],
    cmdclass = {'test': TestCommand},
    long_description = open(normpath(join(dirname(abspath(__file__)), 'README.rst'))).read(),
)
