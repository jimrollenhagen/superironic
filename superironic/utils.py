# Copyright 2015 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from superironic import colors
from superironic import config


def get_envs_in_group(group_name):
    """
    Takes a group_name and finds any environments that have a SUPERIRONIC_GROUP
    configuration line that matches the group_name.
    """
    envs = []
    for section in config.ironic_creds.sections():
        if (config.ironic_creds.has_option(section, 'SUPERIRONIC_GROUP') and
                config.ironic_creds.get(section,
                                      'SUPERIRONIC_GROUP') == group_name):
            envs.append(section)
    return envs


def is_valid_environment(env):
    """Check if config file contains `env`."""
    valid_envs = config.ironic_creds.sections()
    return env in valid_envs


def is_valid_group(group_name):
    """
    Checks to see if the configuration file contains a SUPERIRONIC_GROUP
    configuration option.
    """
    valid_groups = []
    for section in config.ironic_creds.sections():
        if config.ironic_creds.has_option(section, 'SUPERIRONIC_GROUP'):
            valid_groups.append(config.ironic_creds.get(section,
                                                      'SUPERIRONIC_GROUP'))
    valid_groups = list(set(valid_groups))
    if group_name in valid_groups:
        return True
    else:
        return False


def print_valid_envs(valid_envs):
    """Prints the available environments."""
    print("[%s] Your valid environments are:" %
          (colors.gwrap('Found environments')))
    print("%r" % valid_envs)


def warn_missing_ironic_args():
    """Warn user about missing Ironic arguments."""
    msg = """
[%s] No arguments were provided to pass along to ironic.
The superironic script expects to get commands structured like this:

  superironic [environment] [command]

Here are some example commands that may help you get started:

  superironic prod node-list
  superironic prod node-show
  superironic prod port-list
"""
    print(msg % colors.rwrap('Missing arguments'))


def rm_prefix(name):
    """
    Removes ironic_ os_ ironicclient_ prefix from string.
    """
    if name.startswith('ironic_'):
        return name[7:]
    elif name.startswith('ironicclient_'):
        return name[13:]
    elif name.startswith('os_'):
        return name[3:]
    else:
        return name
