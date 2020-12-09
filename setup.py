import os
import re
from os.path import join as join_path

import docker
import setuptools
import zetuptools
from pkg_resources import resource_filename
from setuptools.command.develop import develop
from setuptools.command.install import install

TOOLS = zetuptools.ZetupTools("apt-repo", "Zeke Marffy", "zmarffy@yahoo.com")
PACKAGE = TOOLS.packages["apt_repo"]


class CustomInstall(install):
    def run(self):
        install.run(self)
        PACKAGE.build_docker_images()


class CustomDevelop(develop):
    def run(self):
        develop.run(self)
        PACKAGE.build_docker_images()


setuptools.setup(
    name=TOOLS.name,
    version=PACKAGE.version,
    author=TOOLS.author,
    author_email=TOOLS.author_email,
    packages=setuptools.find_packages(),
    url='https://github.com/zmarffy/apt-repo',
    license='MIT',
    description='Host APT repos on your server or GitHub',
    python_requires=TOOLS.minimum_version_required,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'reequirements',
        'python-magic',
        'pyyaml',
        'tabulate',
        'zmtools>=1.6.0',
        'zetuptools>=1.0.2'
    ],
    entry_points={
        'console_scripts': [
            'apt-repo = apt_repo.__main__:main',
        ],
    },
    package_data=TOOLS.all_files,
    cmdclass={
        'install': CustomInstall,
        'develop': CustomDevelop
    },
    include_package_data=True
)
