# Copyright (C) 2021 Apple Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1.  Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 2.  Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY APPLE INC. AND ITS CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL APPLE INC. OR ITS CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import sys

from .command import Command

from webkitcorepy import run, Terminal
from webkitscmpy import local, log


class Branch(Command):
    name = 'branch'
    help = 'Create a local development branch from the current checkout state'

    PREFIX = 'eng'

    @classmethod
    def parser(cls, parser, loggers=None):
        parser.add_argument(
            '-i', '--issue', '-b', '--bug', '-r',
            dest='issue', type=str,
            help='Number (or name) of the issue or bug to create branch for',
        )

    @classmethod
    def normalize_issue(cls, issue):
        if not issue or issue.startswith(cls.PREFIX):
            return issue
        return '{}/{}'.format(cls.PREFIX, issue)

    @classmethod
    def main(cls, args, repository, **kwargs):
        if not isinstance(repository, local.Git):
            sys.stderr.write("Can only 'branch' on a native Git repository\n")
            return 1

        if not args.issue:
            args.issue = Terminal.input('Branch name: ')
        args.issue = cls.normalize_issue(args.issue)

        if run([repository.executable(), 'check-ref-format', args.issue], capture_output=True).returncode:
            sys.stderr.write("'{}' is an invalid branch name, cannot create it\n".format(args.issue))
            return 1

        remote_re = re.compile('remotes/.+/{}'.format(re.escape(args.issue)))
        for branch in repository.branches:
            if branch == args.issue or remote_re.match(branch):
                sys.stderr.write("'{}' already exists\n".format(args.issue))
                return 1

        log.warning("Creating the local development branch '{}'...".format(args.issue))
        if run([repository.executable(), 'checkout', '-b', args.issue], cwd=repository.root_path).returncode:
            sys.stderr.write("Failed to create '{}'\n".format(args.issue))
            return 1
        repository._branch = args.issue  # Assign the cache because of repository.branch's caching
        print("Created the local development branch '{}'!".format(args.issue))
        return 0
