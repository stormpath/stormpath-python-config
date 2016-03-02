# stormpath-python-config

*Stormpath configuration loader.*


This library is responsible for loading the Stormpath configuration.  It is an 
internal module used by stormpath-sdk-python, stormpath-django and 
stormpath-flask, and is not meant for general consumption.


## Installation

To install this library, just run:

```
$ pip install stormpath-config
```

If this doesn't work, you might need to install `pip` on your computer.  See the
[Pip installation guide](http://www.pip-installer.org/en/latest/installing.html)
for more information.


## Usage

First, you'll need to initialize a new `ConfigLoader` object using the library like so:

```python
from stormpath_config.loader import ConfigLoader

config_loader = ConfigLoader(load_strategies, post_processing_strategies, validation_strategies)
```

All ConfigLoader arguments are lists of strategies:
* `load_strategies` - list of strategies that load config
* `post_processing_strategies` - list of strategies that will be performed after each load strategy
* `validation_strategies` - list of strategies that will be performed after load and post processing strategies are finished

See [strategies](#strategies) for a list of all supported strategies and on how to create your own.

E.g. below demonstrates how the Stormpath configuration can be created and loaded from only the environment.

```python
from stormpath_config.strategies import LoadEnvConfigStrategy, LoadFileConfigStrategy


config_loader = ConfigLoader(
    [
        LoadEnvConfigStrategy(prefix='STORMPATH'),
        LoadFileConfigStrategy('~/stormpath.yml')
    ]);
```

Now, once you got your new `ConfigLoader` object all you need to do is call the `load()` method to load the configuration data.
You can do this like so:

```python
config = config_loader.load()
print(config)
```

## Strategies

### Creating your own strategy

A strategy is simply a prototype that implements a method named `process` that takes the parameter `config` and returns processed config. E.g. as shown below:

```python
class MyConfigStrategy(object):
    def process(self, config=None):
        # Apply strategy to config and return resulting config
        config['someNewField'] = 'abc' # Append someNewField to our config
        return config
```

### Supported

Some default strategies for loading a configuration has been included. These are accessible through the `stormpath_config.strategies` module.

#### LoadEnvConfigStrategy

Loads configuration from the system environment.

#### LoadAPIKeyConfigStrategy

Loads client API key configuration from a .properties file.

#### LoadFileConfigStrategy

Loads a configuration from either a JSON or YAML file.

#### ExtendConfigStrategy

Extend a the configuration with an existing object.

#### LoadAPIKeyFromConfigStrategy

Loads an API key specified in config into the configuration.

#### MoveAPIKeyToClientAPIKeyStrategy

Moves an API key from apiKey to client.apiKey.

#### EnrichClientFromRemoteConfigStrategy

Enriches the configuration with client config resolved from the Stormpath API.

#### EnrichIntegrationConfigStrategy

Enriches the configuration with integration config resolved at runtime.

#### EnrichIntegrationFromRemoteConfigStrategy

Enriches the configuration with integration config resolved from the Stormpath API.

#### ValidateClientConfigStrategy

Validates the client configuration.

#### DebugConfigStrategy

Dumps the config to the provided logger.
    

## Contributing

You can make your own contributions by forking this repository, making your
changes in a feature branch, and then issuing a pull request back to this
repository on the `master` branch.

Here's how you might do this if you wanted to contribute something:

```console
$ git clone https://github.com/stormpath/stormpath-python-config.git
$ cd stormpath-python-config
$ git checkout -b feature-something-something
$ # make changes
$ git commit -m "This was easy!"
$ # submit a pull request
```

We regularly maintain this repository, and are quick to review pull requests
and accept changes!

We <333 contributions!

## Copyright

Copyright &copy;2015 Stormpath, Inc. and contributors.

This project is open-source via the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0).
