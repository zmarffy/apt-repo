import os
import subprocess

import zetuptools


class InstallDirectives(zetuptools.InstallDirectives):

    def _install(self, old_version, new_version):
        self.package.build_docker_images()

    def _uninstall(self, version):
        self.package.remove_docker_images()
        for repo in os.listdir(os.path.join(os.path.expanduser("~"), ".apt-repo")):
            if os.path.isfile(os.path.join(repo, "containerid")):
                subprocess.check_call(
                    ["apt-repo", "serve", "-n", repo, "-s"])
