import os
import re

import setuptools

with open(os.path.join("apt_repo_maker", "__init__.py"), encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

packages = setuptools.find_packages()

setuptools.setup(
    name="apt-repo-maker",
    version=version,
    author="Zeke Marffy",
    author_email="zmarffy@yahoo.com",
    packages=packages,
    url='https://github.com/zmarffy/apt-repo',
    license='MIT',
    description='Host APT repos on your server or GitHub',
    python_requires='>=3.6',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'reequirements',
        'pyyaml',
        'tabulate',
        'zmtools>=1.6.0',
        'zetuptools>=2.2.0'
    ],
    entry_points={
        'console_scripts': [
            'apt-repo = apt_repo_maker.__main__:main',
        ],
    },
    package_data={package: ["*"] for package in packages},
)
