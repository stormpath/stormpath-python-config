stormpath-python-config
=======================

.. image:: https://img.shields.io/pypi/v/stormpath-config.svg
    :alt: stormpath-config Release
    :target: https://pypi.python.org/pypi/stormpath-config

.. image:: https://img.shields.io/pypi/dm/stormpath-config.svg
    :alt: stormpath-config Downloads
    :target: https://pypi.python.org/pypi/stormpath-config

.. image:: https://api.codacy.com/project/badge/grade/4d30e6436ad74e59acb6f9e28977e09b
    :alt: stormpath-config Code Quality
    :target: https://www.codacy.com/app/r/stormpath-python-config

.. image:: https://img.shields.io/travis/stormpath/stormpath-python-config.svg
    :alt: stormpath-python-config Build
    :target: https://travis-ci.org/stormpath/stormpath-python-config

*Stormpath configuration loader.*

.. note::
    This library is responsible for loading Stormpath configuration.  It is an
    internal module used by stormpath-sdk-python, stormpath-django, and
    stormpath-flask, and is not meant for general consumption.


Installation
------------

To install this library, just run:

.. code-block:: console

    $ pip install stormpath-config

If this doesn't work, you might need to install ``pip`` on your computer.  See
the `pip installation guide`_ for more information.


Usage
-----

First, you'll need to initialize a new ``ConfigLoader`` object like so:

.. code-block:: python

    from stormpath_config.loader import ConfigLoader

    config_loader = ConfigLoader(load_strategies, post_processing_strategies, validation_strategies)

All ``ConfigLoader`` arguments are lists of strategies:

* ``load_strategies`` - List of strategies that load configuration data.
* ``post_processing_strategies`` - List of strategies that will be performed
  after each load strategy.
* ``validation_strategies`` - List of strategies that will be performed after
  load and post processing strategies are finished.

See `strategies`_ for a list of all supported strategies, and information about
how to create your own.

Here's an example of how Stormpath configuration data can be loaded from
environment variables:

.. code-block:: python

    from stormpath_config.strategies import LoadEnvConfigStrategy, LoadFileConfigStrategy

    config_loader = ConfigLoader([
        LoadEnvConfigStrategy(prefix='STORMPATH'),
        LoadFileConfigStrategy('~/stormpath.yml'),
    ])

Now, once you have your new ``ConfigLoader`` object, all you need to do is call
the ``load()`` method to load all configuration data.  You can do this like so:

.. code-block:: python
    config = config_loader.load()
    print(config)


Strategies
----------


Creating Your Own Strategy
..........................

A strategy is simply a prototype that implements a method named ``process``
that takes the parameter ``config`` and returns processed ``config``.  For
instance:

.. code-block:: python

    class MyConfigStrategy(object):
        def process(self, config=None):
            # Apply strategy to config and return resulting config.
            config['someNewField'] = 'abc' # Append someNewField to our config
            return config


Supported
.........

Some default strategies for loading configuration data are already built in.
These are accessible through the ``stormpath_config.strategies`` module.


LoadEnvConfigStrategy
`````````````````````

Loads configuration from the system environment.


LoadAPIKeyConfigStrategy
````````````````````````

Loads client API key configuration from a .properties file.


LoadFileConfigStrategy
``````````````````````

Loads configuration from either a JSON or YAML file.


ExtendConfigStrategy
````````````````````

Extends configuration data with an existing object.


LoadAPIKeyFromConfigStrategy
````````````````````````````

Loads an API key from configuration data.


MoveAPIKeyToClientAPIKeyStrategy
````````````````````````````````

Moves an API key from ``apiKey`` to ``client.apiKey``.


EnrichClientFromRemoteConfigStrategy
````````````````````````````````````

Enriches the configuration with client configuration information resolved from
the Stormpath API.


EnrichIntegrationConfigStrategy
```````````````````````````````

Enriches the configuration with integration config resolved at runtime.


EnrichIntegrationFromRemoteConfigStrategy
`````````````````````````````````````````

Enriches the configuration with integration config resolved from the Stormpath
API.


ValidateClientConfigStrategy
````````````````````````````

Validates the client configuration.


DebugConfigStrategy
```````````````````

Dumps the config to the provided logger.


Contributing
------------

You can make your own contributions by forking this repository, making your
changes in a feature branch, and then issuing a pull request back to this
repository on the ``master`` branch.

Here's how you might do this if you wanted to contribute something:

.. code-block:: console

    $ git clone https://github.com/stormpath/stormpath-python-config.git
    $ cd stormpath-python-config
    $ git checkout -b feature-something-something
    $ # make changes
    $ git commit -m "This was easy!"
    $ git push origin feature-something-something
    $ # submit a pull request

We regularly maintain this repository, and are quick to review pull requests
and accept changes!

We <333 contributions!


Copyright
---------

Copyright &copy;2015 Stormpath, Inc. and contributors.


.. _pip installation guide: http://pip.readthedocs.org/en/stable/installing/ "pip Installation Guide"
.. _strategies: #strategies "Stormpath Python Config Strategies"
