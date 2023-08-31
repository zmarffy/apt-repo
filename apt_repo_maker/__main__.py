import argparse
from getpass import getpass
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests
import zmtools
from rich.console import Console
from rich.logging import RichHandler
from tabulate import tabulate

CONSOLE = Console()
LOGGER = logging.getLogger(__name__)

DISTRIBUTIONS_STRING = """Origin: {}
Label: {}
Codename: {}
Architectures: {}
Components: {}
Description: {}
SignWith: {}
"""
GITHUB_BASE_API_URL = "https://api.github.com"
GITHUB_FILE_SIZE_LIMIT_BYTES = 10000000


def _run_command(*args, **kwargs) -> subprocess.CompletedProcess:
    LOGGER.debug(f"Running command: {subprocess.list2cmdline(args[0])}")
    return subprocess.run(*args, **kwargs)


def _get_remote() -> str:
    return _run_command(
        ["git", "config", "--get", "remote.origin.url"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def _get_distributions_text(repo_files_location: Path) -> str:
    with open(Path(repo_files_location, "conf", "distributions"), "r") as f:
        return f.read()


def _get_codename(distributions_text: str) -> str:
    return re.findall(r"(?<=Codename: ).+", distributions_text)[0]


def _get_allarch(distributions_text: str) -> str:
    return re.findall(r"(?<=Architectures: ).+", distributions_text)[0].replace(
        " ", "|"
    )


def _check_exists_and_return_path(p: str) -> Path:
    path = Path(p)
    if path.exists():
        return path
    else:
        raise FileNotFoundError(p) from None


def _deb_file_transform(s: str) -> tuple[str, str, str]:
    f, c = re.search(r"(.+\.deb$)(?::(.+))?", s).groups()
    a = re.findall(
        "(?<=Architecture: ).+",
        _run_command(
            ["dpkg", "--info", f], text=True, capture_output=True, check=True
        ).stdout,
    )[0]
    if c is None:
        c = input(f"{f} component: ")
        if not c:
            raise ValueError("Empty component")
    return f, c, a


def _update_repo(repo_files_location: str, clean: bool = False) -> None:
    with zmtools.working_directory(repo_files_location):
        if clean:
            remote = _get_remote()
            dash_b = ["-b"]
            shutil.rmtree(".git")
            _run_command(["git", "init"], check=True)
            _run_command(
                ["git", "remote", "add", "origin", remote],
                check=True,
            )
        else:
            dash_b = []
        _run_command(
            ["git", "checkout", "-q"] + dash_b + ["gh-pages"],
            check=True,
        )
        _run_command(["git", "add", "--all"], check=True)
        _run_command(
            ["git", "commit", "-m", "update repo", "-a"],
            check=True,
        )
        _run_command(
            ["git", "push", "origin", "gh-pages", "--force"],
            check=True,
        )


def github_request(method: str, endpoint: str, token: str, json: Any = None) -> Any:
    """Return a dict of info about the packages available in the repo.

    Args:
        codename (str): List packages of this codename.
        repo_files_location (str): Location of the repo files.

    Returns:
        list[dict[str, str]]: Info about the packages available.
    """
    r = requests.request(
        method,
        f"{GITHUB_BASE_API_URL}{endpoint}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json=json,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError:
        LOGGER.error(r.text)
        raise
    if r.text:
        return r.json()
    else:
        return None


def list_packages_available(
    codename: str, repo_files_location: str
) -> list[dict[str, str]]:
    """Return a dict of info about the packages available in the repo.

    Args:
        codename (str): List packages of this codename.
        repo_files_location (str): Location of the repo files.

    Returns:
        list[dict[str, str]]: Info about the packages available.
    """
    o = _run_command(
        ["reprepro", "-b", repo_files_location, "list", codename],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if o == "":
        # No debs
        return []
    else:
        # Parse the output and return a list of dicts
        return [
            dict(zip(["codename", "component", "arch", "name", "version"], p))
            for p in [
                b[0].split("|") + b[1].split(" ", 1)
                for b in [d0.split(": ", 1) for d0 in o.split("\n")]
            ]
        ]


def main() -> int:  # noqa: C901
    EXIT_CODE = 0

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="action to take"
    )

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("name")

    setup_parser = subparsers.add_parser(
        "setup",
        help="setup the repo for the first time",
        parents=[parent_parser],
    )
    setup_parser.add_argument(
        "--public-key",
        required=True,
        type=_check_exists_and_return_path,
        help="public key to copy to repo",
    )
    setup_parser.add_argument(
        "--private-key",
        required=True,
        help="private key to sign packages with",
    )
    setup_parser.add_argument("--description", required=True)
    setup_parser.add_argument("--origin", required=True)
    setup_parser.add_argument("--label", required=True)
    setup_parser.add_argument("--codename", required=True)
    setup_parser.add_argument("--arch", nargs="+", required=True)
    setup_parser.add_argument("--component", nargs="+", required=True)
    setup_parser.add_argument(
        "--splash",
        type=_check_exists_and_return_path,
        help="HTML splash page for the repo",
    )
    setup_parser.add_argument(
        "--private", action="store_true", help="make repo private"
    )

    add_parser = subparsers.add_parser(
        "add",
        help="add DEBs to the repo",
        parents=[parent_parser],
    )
    add_parser.add_argument(
        "debs",
        nargs="+",
        type=_check_exists_and_return_path,
        help="DEB files to add (either just their locations, or <location>:<component>)",
    )

    remove_parser = subparsers.add_parser(
        "remove",
        help="remove packages from the repo",
        parents=[parent_parser],
    )
    remove_parser.add_argument("packages", nargs="+", help="packages to remove")

    list_parser = subparsers.add_parser(
        "list",
        help="list DEBs in the repo",
        parents=[parent_parser],
    )
    list_parser.add_argument(
        "--no-format", action="store_true", help="do not pretty-print list"
    )

    subparsers.add_parser(
        "clean",
        help="clean repo by wiping git history",
        parents=[parent_parser],
    )

    args = parser.parse_args()

    if not args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    logging.basicConfig(
        level=log_level,
        format="",
        handlers=[RichHandler(level=log_level, console=CONSOLE)],
    )

    if args.command is None:
        parser.error("Need to specify a command")

    BASE_LOCATION = Path(Path.home(), "apt-repo")
    REPO_FILES_LOCATION = Path(BASE_LOCATION, args.name)

    if args.command != "setup":
        if not REPO_FILES_LOCATION.is_dir():
            raise FileNotFoundError(
                f"{REPO_FILES_LOCATION} does not exist; please run `apt-repo {args.name} setup` first"
            ) from None

    GH_TOKEN = os.getenv("GH_TOKEN") or getpass("Enter GitHub token: ")

    if args.command == "setup":
        # If necessary and the user wants to, completely wipe the repo
        try:
            setup_already = bool(next(REPO_FILES_LOCATION.iterdir(), None))
        except FileNotFoundError:
            setup_already = False
        if setup_already:
            if zmtools.y_to_continue(
                f"Repo already set up at {REPO_FILES_LOCATION}; wipe and start over? (y/n)"
            ) and zmtools.y_to_continue(
                "Are you REALLY sure you want to wipe the repo? There is no going back from this. (y/n)"
            ):
                with zmtools.working_directory(REPO_FILES_LOCATION):
                    github_username, github_repo_name_dot_git = _get_remote().split(
                        "/", 4
                    )[3:5]
                github_request(
                    "DELETE",
                    f"/repos/{github_username}/{github_repo_name_dot_git.removesuffix('.git')}",
                    GH_TOKEN,
                )
                shutil.rmtree(REPO_FILES_LOCATION)

            else:
                sys.exit("Setup aborted")

        # Make directories if necessary
        REPO_FILES_LOCATION.mkdir(parents=True, exist_ok=True)

        # Copy the splash page
        if args.splash:
            if args.private:
                LOGGER.warning(
                    "Ignoring splash value as splash pages are not supported for GitHub private repos"
                )
            else:
                shutil.copy(args.splash, Path(REPO_FILES_LOCATION, "index.html"))

        # Copy the public key
        shutil.copy(args.public_key, Path(REPO_FILES_LOCATION, "repo.key"))

        Path(REPO_FILES_LOCATION, "conf").mkdir(parents=True, exist_ok=True)
        with open(Path(REPO_FILES_LOCATION, "conf", "distributions"), "w") as f:
            f.write(
                DISTRIBUTIONS_STRING.format(
                    args.origin,
                    args.label,
                    args.codename,
                    " ".join(args.arch),
                    " ".join(args.component),
                    args.description,
                    args.private_key,
                )
            )
        with zmtools.working_directory(REPO_FILES_LOCATION):
            _run_command(["git", "init"], check=True)
            clone_url = github_request(
                "POST",
                "/user/repos",
                GH_TOKEN,
                json={
                    "name": args.name,
                    "description": args.description,
                    "private": args.private,
                    "has_issues": False,
                    "has_projects": False,
                    "has_wiki": False,
                },
            )["clone_url"]
            _run_command(["git", "remote", "add", "origin", clone_url], check=True)
            _run_command(
                ["git", "checkout", "-q", "-b", "gh-pages"],
                check=True,
            )
            _run_command(["git", "add", "--all"], check=True)
            _run_command(
                ["git", "commit", "-m", "set up repo", "-a"],
                check=True,
            )
            _run_command(
                ["git", "push", "origin", "gh-pages"],
                check=True,
            )

    elif args.command == "add":
        debs = [_deb_file_transform(str(deb)) for deb in args.debs]
        distributions_text = _get_distributions_text(REPO_FILES_LOCATION)
        codename = _get_codename(distributions_text)
        if not Path(REPO_FILES_LOCATION, "db").is_dir():
            # First time run edge case
            original_debs_list = []
        else:
            original_debs_list = list_packages_available(codename, REPO_FILES_LOCATION)
        for deb_file, component, arch_ in debs:
            try:
                if Path(deb_file).stat().st_size > GITHUB_FILE_SIZE_LIMIT_BYTES:
                    EXIT_CODE = 2
                    LOGGER.warning(f"{deb_file} exceeds 100 MB; cannot add to repo")
                if arch_ == "all":
                    arch = _get_allarch(distributions_text)
                else:
                    arch = arch_
                _run_command(
                    [
                        "reprepro",
                        "--ask-passphrase",
                        "-C",
                        component,
                        "-A",
                        arch,
                        "-Vb",
                        REPO_FILES_LOCATION,
                        "includedeb",
                        codename,
                        deb_file,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError:
                LOGGER.exception(
                    "reprepro error! You may have to resolve the issues by running reprepro commands manually"
                )
                EXIT_CODE = 2
        new_debs_list = [
            deb
            for deb in list_packages_available(codename, REPO_FILES_LOCATION)
            if deb not in original_debs_list
        ]
        if new_debs_list:
            LOGGER.info("New DEBs added")
            print(tabulate(new_debs_list, headers="keys"))
            _update_repo(REPO_FILES_LOCATION)
        else:
            LOGGER.warning("No new DEBs added")
            EXIT_CODE = 1

    elif args.command == "remove":
        codename = _get_codename(_get_distributions_text(REPO_FILES_LOCATION))
        original_debs_list = list_packages_available(codename, REPO_FILES_LOCATION)
        try:
            _run_command(
                [
                    "reprepro",
                    "-Vb",
                    REPO_FILES_LOCATION,
                    "remove",
                    codename,
                ]
                + args.packages,
                check=True,
            )
        except subprocess.CalledProcessError:
            LOGGER.exception(
                "reprepro error! You may have to resolve the issues by running reprepro commands manually"
            )
            EXIT_CODE = 2
        removed_debs_list = [
            deb
            for deb in original_debs_list
            if deb not in list_packages_available(codename, REPO_FILES_LOCATION)
        ]
        if removed_debs_list:
            LOGGER.info("DEBs removed")
            print(tabulate(removed_debs_list, headers="keys"))
            # Push to GitHub
            _update_repo(REPO_FILES_LOCATION)
        else:
            LOGGER.warning("No DEBs removed")
            EXIT_CODE = 2

    elif args.command == "list":
        codename = _get_codename(_get_distributions_text(REPO_FILES_LOCATION))
        debs = list_packages_available(codename, REPO_FILES_LOCATION)
        if debs:
            if not args.no_format:
                print(tabulate(debs, headers="keys"))
            else:
                for deb in debs:
                    print(" ".join([v for v in deb.values()]).strip())
        else:
            LOGGER.info(f'No DEBs in repo "{args.name}" yet')

    elif args.command == "clean":
        # Completely reset the entire repo
        _update_repo(REPO_FILES_LOCATION, clean=True)

    return EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
