import argparse
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

import zmtools
from tabulate import tabulate

LOGGER = logging.getLogger()

DISTRIBUTIONS_STRING = """Origin: {}
Label: {}
Codename: {}
Architectures: {}
Components: {}
Description: {}
SignWith: {}
"""


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
        raise FileNotFoundError(p)


def _deb_file_transform(s: str) -> tuple[str, str, str]:
    f, c = re.search(r"(.+\.deb$)(?::(.+))?", s).groups()
    a = re.findall(
        "(?<=Architecture: ).+",
        subprocess.run(["dpkg", "--info", f], capture_output=True, text=True).stdout,
    )[0]
    if c is None:
        c = input(f"{f} component: ")
        if not c:
            raise ValueError("Empty component")
    return f, c, a


def _update_repo(repo_files_location: str, clean: bool = False) -> None:
    with zmtools.working_directory(repo_files_location):
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"]
        )
        if clean:
            dash_b = ["-b"]
            shutil.rmtree(".git")
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "remote", "add", "origin", remote], check=True)
        else:
            dash_b = []
        subprocess.run(["git", "checkout", "-q"] + dash_b + ["gh-pages"], check=True)
        subprocess.run(["git", "add", "--all"], check=True)
        subprocess.run(["git", "commit", "-m", "update repo", "-a"], check=True)
        subprocess.run(["git", "push", "origin", "gh-pages", "--force"], check=True)


def list_packages_available(
    codename: str, repo_files_location: str
) -> list[dict[str, str]]:
    """Return a dict of info about the packages available in the repo.

    Args:
        codename (str): List packages of this codename.
        repo_files_location (str): Location of the repo files.

    Returns:
        List[Dict[str, str]]: Info about the packages available.
    """
    o = subprocess.run(
        ["reprepro", "-b", repo_files_location, "list", codename],
        capture_output=True,
        text=True,
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


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument("name")

    subparsers = parser.add_subparsers(dest="command", help="action to take")

    setup_parser = subparsers.add_parser(
        "setup", help="setup the repo for the first time"
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

    add_packages_parser = subparsers.add_parser(
        "add-packages", help="add DEBs to the repo"
    )
    add_packages_parser.add_argument(
        "debs",
        nargs="+",
        type=lambda x: _deb_file_transform(str(_check_exists_and_return_path(x))),
        help="DEB files to add (either just their locations, or <location>:<component>)",
    )

    remove_packages_parser = subparsers.add_parser(
        "remove-packages", help="remove packages from the repo"
    )
    remove_packages_parser.add_argument(
        "packages", nargs="+", help="packages to remove"
    )

    list_packages_parser = subparsers.add_parser(
        "list-packages", help="list DEBs in the repo"
    )
    list_packages_parser.add_argument(
        "--no-format", action="store_true", help="do not pretty-print list"
    )

    subparsers.add_parser("clean", help="clean repo (may take a while)")

    args = parser.parse_args()

    if args.command is None:
        parser.error("Need to specify a command")

    BASE_LOCATION = Path(Path.home(), "apt-repo")
    REPO_NAME_BASE_LOCATION = Path(BASE_LOCATION, args.name)

    if args.command != "setup":
        if not REPO_NAME_BASE_LOCATION.is_dir():
            raise FileNotFoundError(
                f"{REPO_NAME_BASE_LOCATION} does not exist; please run `apt-repo {args.name} setup` first"
            )

    REPO_FILES_LOCATION = Path(REPO_NAME_BASE_LOCATION, "repo_files")

    if args.command == "setup":
        # If necessary and the user wants to, completely wipe the repo
        try:
            setup_already = bool(next(REPO_FILES_LOCATION.iterdir(), None))
        except FileNotFoundError:
            setup_already = False
        if setup_already:
            if zmtools.y_to_continue(
                f"Repo already set up at {REPO_NAME_BASE_LOCATION}; wipe and start over? (y/n)"
            ) and zmtools.y_to_continue(
                "Are you REALLY sure you want to wipe the repo? There is no going back from this. (y/n)"
            ):
                shutil.rmtree(REPO_NAME_BASE_LOCATION)
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
        if args.private:
            repo_type = "private"
        else:
            repo_type = "public"
        with zmtools.working_directory(REPO_FILES_LOCATION):
            subprocess.run(["git", "init"], check=True)
            subprocess.run(
                [
                    "gh",
                    "repo",
                    "create",
                    args.name,
                    f"--{repo_type}",
                    "--description",
                    args.description,
                    "--disable-issues",
                    "--disable-wiki",
                    "--source=.",
                    "--remote=origin",
                ],
                check=True,
            )
            subprocess.run(["git", "checkout", "-q", "-b", "gh-pages"], check=True)
            subprocess.run(["git", "add", "--all"], check=True)
            subprocess.run(["git", "commit", "-m", "set up repo", "-a"], check=True)
            subprocess.run(["git", "push", "origin", "gh-pages"], check=True)

    elif args.command == "add-packages":
        distributions_text = _get_distributions_text(REPO_FILES_LOCATION)
        codename = _get_codename(distributions_text)
        if not Path(REPO_FILES_LOCATION, "db").is_dir():
            # First time run edge case
            original_debs_list = []
        else:
            original_debs_list = list_packages_available(codename, REPO_FILES_LOCATION)
        for deb_file, component, arch_ in args.debs:
            if Path(deb_file).stat().st_size > 10000000:
                LOGGER.warning(f"{deb_file} exceeds 100 MB; cannot add to repo")
            if arch_ == "all":
                arch = _get_allarch(distributions_text)
            else:
                arch = arch_
            subprocess.run(
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

    elif args.command == "remove-packages":
        codename = _get_codename(_get_distributions_text(REPO_FILES_LOCATION))
        original_debs_list = list_packages_available(codename, REPO_FILES_LOCATION)
        for package in args.packages:
            subprocess.run(
                [
                    "reprepro",
                    "-Vb",
                    REPO_FILES_LOCATION,
                    "remove",
                    codename,
                    package,
                ],
                check=True,
            )
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

    elif args.command == "list-packages":
        codename = _get_codename(_get_distributions_text(REPO_FILES_LOCATION))
        debs = list_packages_available(codename, REPO_FILES_LOCATION)
        if debs:
            if not args.no_format:
                print(tabulate(debs, headers="keys"))
            else:
                for deb in debs:
                    print(" ".join([v for v in deb.values()]).strip())
        else:
            LOGGER.warning(f'No DEBs in repo "{args.name}" yet')

    elif args.command == "clean":
        # Completely reset the entire repo
        _update_repo(REPO_FILES_LOCATION, clean=True)

    else:
        parser.print_help()
        parser.error("Invalid command")

    return 0


if __name__ == "__main__":
    sys.exit(main())
