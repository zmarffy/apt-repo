import os
import docker
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

    def __init__(self) -> None:
        super().__init__("apt-repo-maker", data_folder=os.path.join(os.path.expanduser("~"),
                                                                    ".apt-repo"), docker_images=["apt-repo"])

    def _install(self, old_version, new_version) -> None:
        # Two data folders because I made this a long time ago
        os.makedirs(os.path.join(os.path.expanduser(
            "~"), "apt-repo"), exist_ok=True)
        self.build_docker_images()

    def _uninstall(self, version) -> None:
        self.remove_docker_images()
        shutil.rmtree(os.path.join(os.path.expanduser("~"), "apt-repo"))
