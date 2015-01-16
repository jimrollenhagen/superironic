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

import argparse
import sys

import pkg_resources

from superironic import colors
from superironic import config
from superironic import credentials
from superironic import utils
from superironic import super_ironic


# Note(tr3buchet): this is necessary to prevent argparse from requiring the
#                  the 'env' parameter when using -l or --list
class _ListAction(argparse._HelpAction):
    """ListAction used for the -l and --list arguments."""
    def __call__(self, parser, *args, **kwargs):
        """Lists are configured superironic environments."""
        for ironic_env in config.ironic_creds.sections():
            envheader = '-- %s ' % colors.gwrap(ironic_env)
            print(envheader.ljust(86, '-'))
            for param, value in sorted(config.ironic_creds.items(ironic_env)):
                print('  %s: %s' % (param.upper().ljust(21), value))
        parser.exit()


# Copying tr3buchet's hack to short circuit argparse and display the
# version number of superironic
class _ShowVersion(argparse._HelpAction):
    """_ShowVersion used for the --version argument."""
    def __call__(self, parser, *args, **kwargs):
        version = pkg_resources.require("superironic")[0].version
        print("superironic %s" % version)
        parser.exit()


def run_superironic():
    """Do prep work and error checking for superironic executable."""

    config.run_config()

    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--executable', default='ironic',
                        help='command to run instead of ironic')
    parser.add_argument('--version', action=_ShowVersion,
                        help='display superironic version')
    parser.add_argument('-l', '--list', action=_ListAction,
                        help='list all configured environments')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='show ironicclient debug output')
    parser.add_argument('env',
                        help=('environment to run ironic against. '
                              'valid options: %s' %
                              sorted(config.ironic_creds.sections())))

    # Allow for passing --options all the way through to ironicclient
    superironic_args, ironic_args = parser.parse_known_args()

    # Did we get any arguments to pass on to ironic?
    if not ironic_args:
        utils.warn_missing_ironic_args()
        sys.exit(1)

    # Is our environment argument a single environment or a superironic group?
    if utils.is_valid_group(superironic_args.env):
        envs = utils.get_envs_in_group(superironic_args.env)
    else:
        envs = [superironic_args.env]

    for env in envs:
        snobj = super_ironic.SuperIronic()
        snobj.ironic_env = env
        returncode = snobj.run_ironicclient(ironic_args, superironic_args)

    # NOTE(major): The return code here is the one that comes back from the
    # OS_EXECUTABLE that superironic runs (by default, 'ironic').  When using
    # superironic groups, the return code is the one returned by the executable
    # for the last environment in the group.
    #
    # It's not ideal, but it's all I can think of for now. ;)
    sys.exit(returncode)


def run_superironic_keyring():
    """
    Handles all of the prep work and error checking for the
    superironic-keyring executable.
    """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-g', '--get', action='store_true',
                       dest='get_password',
                       help='retrieves credentials from keychain storage')
    group.add_argument('-s', '--set', action='store_true',
                       dest='set_password',
                       help='stores credentials in keychain storage')
    parser.add_argument('env',
                        help='environment to set parameter in')
    parser.add_argument('parameter',
                        help='parameter to set')
    args = parser.parse_args()

    if args.set_password:
        credentials.set_user_password(args)

    if args.get_password:
        credentials.get_user_password(args)
