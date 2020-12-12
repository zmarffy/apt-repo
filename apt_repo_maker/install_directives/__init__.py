import zetuptools


class InstallDirectives(zetuptools.InstallDirectives):

    def _install(self, old_version, new_version):
        self.package.build_docker_images()

    # Eventually make uninstall, which should remove the Docker images
