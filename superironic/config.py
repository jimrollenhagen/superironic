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

import os
import sys

from six.moves import configparser

from superironic import colors

ironic_creds = None


def run_config():
    """Runs sanity checks and prepares the global ironic_creds variable."""
    global ironic_creds
    check_environment_presets()
    ironic_creds = load_superironic_config()


def check_environment_presets():
    """Checks for environment variables that can conflict with superironic."""
    presets = [x for x in os.environ.copy().keys()
               if x.startswith('IRONIC') or x.startswith('OS_')]
    if presets:
        print("_" * 80)
        print("*WARNING* Found existing environment variables that may "
              "cause conflicts:")
        for preset in presets:
            print("  - %s" % preset)
        print("_" * 80)


def load_superironic_config():
    """Pulls the superironic configuration file and reads it."""
    xdg_config_home = (os.environ.get('XDG_CONFIG_HOME') or
                       os.path.expanduser('~/.config'))
    possible_configs = [os.path.join(xdg_config_home, "superironic"),
                        os.path.expanduser("~/.superironic"),
                        ".superironic"]
    superironic_config = configparser.RawConfigParser()

    # Can we successfully read the configuration file?
    try:
        superironic_config.read(possible_configs)
    except Exception:
        msg = """
[%s] A valid superironic configuration file is required.
Ensure that you have a properly configured superironic configuration file
called '.superironic' in your home directory or in your current working
directory.
""" % colors.rwrap('Invalid configuration file')
        print(msg)
        sys.exit(1)

    return superironic_config
