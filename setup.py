import os
from os.path import join as join_path

import docker
import setuptools
import zetuptools
from pkg_resources import resource_filename

TOOLS = zetuptools.SetuptoolsExtensions("apt-repo-maker", "Zeke Marffy", "zmarffy@yahoo.com")


setuptools.setup(
    name=TOOLS.name,
    version=TOOLS.version,
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
        'zetuptools>=2.1.0'
    ],
    entry_points={
        'console_scripts': [
            'apt-repo = apt_repo_maker.__main__:main',
        ],
    },
    package_data=TOOLS.all_files,
)
