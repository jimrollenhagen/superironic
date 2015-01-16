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
import re
import subprocess
import sys

from ironicclient import client as ironicclient

from superironic import colors
from superironic import utils
from superironic import config
from superironic import credentials


class SuperIronic(object):
    """
    Gathers information for ironicclient and eventually runs it
    """

    def __init__(self):
        config.run_config()
        self.ironic_env = None
        self.env = os.environ.copy()

    def prep_ironic_creds(self):
        """
        Finds relevant config options in the superironic config and cleans them
        up for ironicclient.
        """
        try:
            raw_creds = config.ironic_creds.items(self.ironic_env)
        except:
            msg = "[%s] Unable to locate section '%s' in your configuration."
            print(msg % (colors.rwrap("Failed"), self.ironic_env))
            sys.exit(1)
        ironic_re = re.compile(r"(^ironic_|^os_|^ironicclient|^trove_)")
        proxy_re = re.compile(r"(^http_proxy|^https_proxy)")

        creds = []
        for param, value in raw_creds:

            # Skip parameters we're unfamiliar with
            if not ironic_re.match(param) and not proxy_re.match(param):
                continue

            if not proxy_re.match(param):
                param = param.upper()

            # Get values from the keyring if we find a USE_KEYRING constant
            if value.startswith("USE_KEYRING"):
                username, credential = credentials.pull_env_credential(
                    self.ironic_env, param, value)
            else:
                credential = value.strip("\"'")

            # Make sure we got something valid from the configuration file or
            # the keyring
            if not credential:
                msg = """
While connecting to %s, superironic attempted to retrieve a credential
for %s but couldn't find it within the keyring.  If you haven't stored
credentials for %s yet, try running:

    superironic-keyring -s %s
""" % (self.ironic_env, username, username, ' '.join(username.split(':')))
                print(msg)
                sys.exit(1)

            creds.append((param, credential))

        return creds

    def prep_shell_environment(self):
        """
        Appends new variables to the current shell environment temporarily.
        """
        for key, value in self.prep_ironic_creds():
            self.env[key] = value

    def prep_extra_args(self):
        """
        Return a list of extra args that need to be passed on cmdline to ironic.
        """
        try:
            raw_creds = config.ironic_creds.items(self.ironic_env)
        except:
            msg = "[%s] Unable to locate section '%s' in your configuration."
            print(msg % (colors.rwrap("Failed"), self.ironic_env))
            sys.exit(1)

        args = []
        for param, value in raw_creds:
            param = param.upper()
            if param == 'BYPASS_URL':
                args += ['--bypass-url', value]

        return args

    def run_ironicclient(self, ironic_args, superironic_args):
        """
        Sets the environment variables for ironicclient, runs ironicclient, and
        prints the output.

        NOTE(major): The name of this method is a bit misleading.  By using the
        OS_EXECUTABLE environment variable or the -x argument, a user can
        specify a different executable to be used other than the default, which
        is 'ironic'.
        """
        # Get the environment variables ready
        self.prep_shell_environment()

        # Check for a debug override
        if superironic_args.debug:
            ironic_args.insert(0, '--debug')

        # Check for OS_EXECUTABLE
        try:
            if self.env['OS_EXECUTABLE']:
                superironic_args.executable = self.env['OS_EXECUTABLE']
        except KeyError:
            pass

        # Print a small message for the user
        msg = "Running %s against %s..." % (superironic_args.executable,
                                            self.ironic_env)
        print("[%s] %s " % (colors.gwrap('superironic'), msg))

        ironic_args = self.prep_extra_args() + ironic_args

        # Call ironicclient and connect stdout/stderr to the current terminal
        # so that any unicode characters from ironicclient's list will be
        # displayed appropriately.
        #
        # In other news, I hate how python 2.6 does unicode.
        process = subprocess.Popen([superironic_args.executable] + ironic_args,
                                   stdout=sys.stdout,
                                   stderr=sys.stderr,
                                   env=self.env)

        # Don't exit until we're sure the subprocess has exited
        process.wait()
        return process.returncode

    def get_ironicclient(self, env, client_version=1):
        """
        Returns python ironicclient object authenticated with superironic config.
        """
        self.ironic_env = env
        assert utils.is_valid_environment(env), "Env %s not found in "\
            "superironic configuration file." % env
        version, creds = self.prep_python_creds(client_version)
        return ironicclient.Client(version, **creds)

    def prep_python_creds(self, client_version=1):
        """
        Prepare credentials for python Client instantiation.
        """
        creds = dict((utils.rm_prefix(k[0].lower()), k[1])
                     for k in self.prep_ironic_creds())
        if creds.get('url'):
            creds['auth_url'] = creds.pop('url')
        if creds.get('tenant_name'):
            creds['project_id'] = creds.pop('tenant_name')
        if creds.get('compute_api_version'):
            client_version = creds.pop('compute_api_version')

        if client_version == '1.1':
            if creds.get('password'):
                creds['api_key'] = creds.pop('password')

        return (client_version, creds)
