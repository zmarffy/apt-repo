import os
import subprocess
import shutil

import zetuptools
from reequirements import Requirement

REQUIREMENTS = [
    Requirement("docker", ["docker", "-v"]),
    Requirement("reprepro", ["reprepro", "--version"]),
    Requirement("gpg", ["gpg", "--version"]),
    Requirement("GitHub CLI", ["gh", "--version"])
]

for requirement in REQUIREMENTS:
    requirement.check()


class InstallDirectives(zetuptools.InstallDirectives):

    package_name = "apt-repo-maker"

    def _install(self, old_version, new_version):
        self.build_docker_images()

    def _uninstall(self, version):
        for repo in os.listdir(os.path.join(os.path.expanduser("~"), ".apt-repo")):
            if os.path.isfile(os.path.join(os.path.join(os.path.expanduser("~"), ".apt-repo", repo, "containerid"))):
                subprocess.check_call(
                    ["apt-repo", "-n", repo, "serve", "-s"])
        shutil.rmtree(os.path.join(os.path.expanduser("~"),
                                   "apt-repo"))  # The other data folder
        self.remove_docker_images()
