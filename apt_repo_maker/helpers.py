import re
import subprocess
from typing import Dict, List

from .constants import LIST_OUTPUT_KEYS


def _deb_file_transform(s: str):
    """From a string formatted like "<filename>" or "<filename>:<component>", return a DEB file's name and component, and if the component is not specified, ask for it.

    Args:
        s (str): The string to parse

    Raises:
        ValueError: If the user does not specify a component when asked to

    Returns:
        Tuple[str, str, str]: The filename, component, and architecture of the DEB file
    """
    f, c = re.search(r"(.+\.deb)(?::(.+))?", s).groups()
    a = determine_arch(f)
    if c is None:
        c = input(f"{f} component: ")
        if not c:
            raise ValueError("Empty component")
    return f, c, a


def list_packages_available(codename: str, repo_files_location: str) -> List[Dict[str, str]]:
    """Return a dict of info about the packages available in the repo

    Args:
        codename (str): List packages of this codename
        repo_files_location (str): Location of the repo files

    Returns:
        List[Dict[str, str]]: Info about the packages available
    """
    o = subprocess.check_output(
        ["reprepro", "-b", repo_files_location, "list", codename]).decode().strip()
    if o == "":
        # No debs
        return []
    else:
        # Parse the output and return a list of dicts
        return [dict(zip(LIST_OUTPUT_KEYS, p)) for p in [b[0].split("|") + b[1].split(" ", 1) for b in [d0.split(": ", 1) for d0 in o.split("\n")]]]


def determine_arch(deb_file: str) -> str:
    """Determine the architecture of a DEB file

    Args:
        deb_file (str): Location of DEB file

    Returns:
        str: The architecture
    """
    return re.findall("(?<=Architecture: ).+", subprocess.check_output(["dpkg", "--info", deb_file]).decode())[0]
