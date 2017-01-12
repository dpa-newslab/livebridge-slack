# livebridge-slack

[![Build Status](https://travis-ci.org/dpa-newslab/livebridge-slack.svg?branch=master)](https://travis-ci.org/dpa-newslab/livebridge-slack)
[![Coverage Status](https://coveralls.io/repos/github/dpa-newslab/livebridge-slack/badge.svg?branch=master)](https://coveralls.io/github/dpa-newslab/livebridge-slack?branch=master)
[![PyPi](https://badge.fury.io/py/livebridge-slack.svg)](https://pypi.python.org/pypi/livebridge-slack)

A [Slack](https://slack.com) plugin for [Livebridge](https://github.com/dpa-newslab/livebridge).

It allows to use Slack channels as source and target for [Livebridge](https://github.com/dpa-newslab/livebridge). 

[Converters](livebridge_slack/converters/) from Liveblog to Slack and from Slack to Scribblelive are also part of this plugin.

## Installation
**Python>=3.5** is needed.
```sh
pip3 install livebridge-slack
```
The plugin will be automatically detected and included from **livebridge** at start time, but it has to be available in **[PYTHONPATH](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)**.

See https://pythonhosted.org/livebridge/plugins.html#installing-plugins for more infos.

## Plugin specific control file parameters
Under **auth:**
* **token** - your Slackbot token

Under **bridges:** and **targets**:
* **type: "slack"**
* **channel** - Slack channel name

**Example:**
```
auth:
    slack:
        token: "abcdef-012345678909876543231"
bridges:
    - source_id: "56fceedda505e600f7195cch"
      endpoint: "https://liveblog.pro/api/"
      type: "liveblog"
      label: "Example"
      targets:
        - type: "slack"
          channel: "channelname"
          auth: "slack"
    # as source
    - channel: "slackchannel"
      type: "slack"
      label: "Channel label"
      targets:
        - type: "acme"
          source_id: "12345"
```

See https://pythonhosted.org/livebridge/control.html for more infos.


## Testing
**Livebridge** uses [py.test](http://pytest.org/) and [asynctest](http://asynctest.readthedocs.io/) for testing.

Run tests:

```sh
    py.test -v tests/
```

Run tests with test coverage:

```sh
    py.test -v --cov=livebridge_slack --cov-report=html tests/
```

[pytest-cov](https://pypi.python.org/pypi/pytest-cov) has to be installed. In the example above, a html summary of the test coverage is saved in **./htmlcov/**.

## License
Copyright 2016 dpa-infocom GmbH

Apache License, Version 2.0 - see LICENSE for details
