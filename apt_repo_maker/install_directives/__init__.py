import os
import subprocess

import zetuptools


class InstallDirectives(zetuptools.InstallDirectives):

    def _install(self, old_version, new_version):
        self.package.build_docker_images()

    def _uninstall(self, version):
        for repo in os.listdir(os.path.join(os.path.expanduser("~"), ".apt-repo")):
            if os.path.isfile(os.path.join(os.path.join(os.path.expanduser("~"), ".apt-repo", repo, "containerid"))):
                subprocess.check_call(
                    ["apt-repo", "-n", repo, "serve", "-s"])
        self.package.remove_docker_images()
