__version__ = "0.3.0"

from reequirements import Requirement

REQUIREMENTS = [
    Requirement("docker", ["docker", "-v"]),
    Requirement("reprepro", ["reprepro", "--version"]),
    Requirement("gpg", ["gpg", "--version"]),
    Requirement("GitHub CLI", ["gh", "--version"])
]

for requirement in REQUIREMENTS:
    requirement.check()
