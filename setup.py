from setuptools import setup, find_packages, Command
import sys
import os
import subprocess

from stormpath import __version__


PY_VERSION = sys.version_info[:2]


class BaseCommand(Command):
    user_options = []

    def pytest(self, *args):
        ret = subprocess.call(
            [
                "py.test",
                "--quiet",
                "--cov-report=term-missing",
                "--cov",
                "stormpath_config"
            ] + list(args))
        sys.exit(ret)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class TestCommand(BaseCommand):

    description = "run self-tests"

    def run(self):
        self.pytest('tests')


class TestDepCommand(BaseCommand):

    description = "install test dependencies"

    def run(self):
        cmd = ["pip", "install", "pytest", "pytest-cov", "stormpath", "mock"]
        ret = subprocess.call(cmd)
        sys.exit(ret)


class DocCommand(BaseCommand):

    description = "generate documentation"

    def run(self):
        try:
            os.chdir('docs')
            ret = os.system('make html')
            sys.exit(ret)
        except OSError as e:
            print(e)
            sys.exit(-1)

# To install the stormpath library, open a Terminal shell, then run this
# file by typing:
#
# python setup.py install

setup(
    name = 'stormpath-config',
    version = __version__,
    description = 'Official Stormpath library, used for loading the Stormpath configuration.',
    author = 'Stormpath, Inc.',
    author_email = 'python@stormpath.com',
    url = 'https://github.com/stormpath/stormpath-python-config',
    zip_safe = False,
    keywords = ['stormpath', 'configuration'],
    install_requires = [
        'flatdict>=1.2.0',
        'pyyaml>=3.11',
    ],
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
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Security',
        'Topic :: Security :: Cryptography',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
    ],
    cmdclass = {
        'test': TestCommand,
        'testdep': TestDepCommand,
        'docs': DocCommand,
    },
    long_description="""\
    Stormpath SDK
    -------------
    DESCRIPTION
    The Stormpath Python Config is responsible for loading the Stormpath
    configuration. It is an internal module used by stormpath-python-sdk,
    stormpath-django, stormpath-flask, and is not meant for general
    consumption.
    LICENSE
    The Stormpath Python Config is distributed under the Apache Software
    License.
    """,
)
