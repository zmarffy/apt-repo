import re
from os.path import join as join_path

import setuptools

with open(join_path("apt_repo", "__init__.py"), encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setuptools.setup(
    name='apt-repo',
    version=version,
    author='Zeke Marffy',
    author_email='zmarffy@yahoo.com',
    packages=setuptools.find_packages(),
    url='https://github.com/zmarffy/apt-repo',
    license='MIT',
    description='Host APT reposon your server or GitHub',
    python_requires='>=3.6',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        "reequirements",
        'python-magic',
        'pyyaml',
        'zmtools>=1.6.0'
    ],
    entry_points={
        'console_scripts': [
            'apt-repo = apt_repo.__main__:main',
        ],
    },
)
