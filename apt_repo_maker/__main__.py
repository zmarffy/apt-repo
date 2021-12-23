import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import uuid

import docker
import yaml
import zetuptools
import zmtools
from tabulate import tabulate

from .helpers import _deb_file_transform, list_packages_available

LOGGER = logging.getLogger()

VALID_HOSTS = [
    "local",
    "github",
    "github-private"
]

DISTRIBUTIONS_STRING = """Origin: {}
Label: {}
Codename: {}
Architectures: {}
Components: {}
Description: {}
SignWith: {}
"""


def main() -> int:

    zmtools.init_logging()

    if not os.path.isdir(os.path.join(os.path.expanduser("~"), ".python_installdirectives", "apt-repo-maker")):
        raise zetuptools.InstallDirectivesNotYetRunException()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n", "--name", help="repo name (overridden by config's \"name\" key)")

    subparsers = parser.add_subparsers(dest="command", help="action to take")

    setup_parser = subparsers.add_parser(
        "setup", help="setup the repo for the first time")
    setup_parser.add_argument(
        "config", type=os.path.abspath, help="config YAML file location")

    serve_parser = subparsers.add_parser(
        "serve", help="start serving the repo")
    serve_parser.add_argument(
        "-s", "--stop", action="store_true", help="stop serving repo")

    add_packages_parser = subparsers.add_parser(
        "add_packages", help="add DEBs to the repo")
    add_packages_parser.add_argument("deb_files", nargs="+", type=_deb_file_transform,
                                     help="DEB files to add (either just their locations, or <location>:<component>)")

    remove_packages_parser = subparsers.add_parser(
        "remove_packages", help="removes packages from the repo")
    remove_packages_parser.add_argument(
        "packages", nargs="+", help="packages to remove")

    list_packages_parser = subparsers.add_parser(
        "list_packages", help="list DEBs in the repo")
    list_packages_parser.add_argument(
        "--no_format", action="store_true", help="do not pretty-print list")

    subparsers.add_parser(
        "clean", help="clean GitHub-hosted repo (may take a while)")

    args = parser.parse_args()

    if args.command is None:
        parser.error("Need to specify a command")

    NAME = args.name
    name_from_config = False

    # TODO: A massive refactor, breaking these actions out into functions
    if args.command == "setup":
        with open(args.config, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        # Validate settings
        if config["host"] not in VALID_HOSTS:
            raise ValueError(
                f"Invalid value \"{config['host']}\" for key \"host\"")
        is_github = "github" in config["host"]
        port_specified = config.get("port") is not None
        ssl_specified = config.get("ssl") is not None
        if port_specified:
            if is_github:
                LOGGER.warning(
                    "Ignoring port value as port does not make sense in the context of GitHub repos")
                config["port"] = None
        if is_github:
            if ssl_specified:
                LOGGER.warning(
                    "Ignoring ssl value as ssl does not make sense in the context of GitHub repos")
                config["ssl"] = None
            if "private" in config["host"] and config.get("splash") is not None:
                LOGGER.warning(
                    "Ignoring splash value as splash pages are not supported for GitHub private repos")
                config["splash"] = None
        else:
            if not port_specified:
                if ssl_specified:
                    config["port"] = 443
                else:
                    config["port"] = 80
        try:
            # Ignore -n
            NAME = config["name"]
            name_from_config = True
        except KeyError:
            pass

    BASE_LOCATION = os.path.join(os.path.expanduser("~"), "apt-repo")

    if args.command != "setup":
        if not os.path.isdir(BASE_LOCATION):
            raise FileNotFoundError(
                f"{BASE_LOCATION} does not exist; please run apt-repo setup first")

    if not name_from_config and NAME is None:
        NAME = zmtools.picker(os.listdir(BASE_LOCATION), "repo")

    REPO_NAME_BASE_LOCATION = os.path.join(BASE_LOCATION, NAME)

    REPO_FILES_LOCATION = os.path.join(REPO_NAME_BASE_LOCATION, "repo_files")
    APACHE_FILES_LOCATION = os.path.join(
        REPO_NAME_BASE_LOCATION, "apache_files")
    DOTAPTREPO_LOCATION = os.path.join(
        os.path.expanduser("~"), ".apt-repo", NAME)
    REPO_SETTINGS_LOCATION = os.path.join(
        DOTAPTREPO_LOCATION, "settings.yaml")

    if args.command == "setup":
        # Completely wipe the repo if the user wants to
        try:
            setup_already = bool(os.listdir(REPO_FILES_LOCATION))
        except FileNotFoundError:
            setup_already = False
        if setup_already:
            if zmtools.y_to_continue(f"Repo already set up at {REPO_FILES_LOCATION}; wipe and start over? (y/n)") and zmtools.y_to_continue("Are you REALLY sure you want to wipe the repo? There is no going back from this. (y/n)"):
                # If this doesn't work, it's probably not your repo :)
                shutil.rmtree(REPO_NAME_BASE_LOCATION)
                shutil.rmtree(DOTAPTREPO_LOCATION)
            else:
                sys.exit("Setup aborted")
        # Make directories if necessary
        os.makedirs(REPO_FILES_LOCATION, exist_ok=True)
        os.makedirs(APACHE_FILES_LOCATION, exist_ok=True)
        os.makedirs(DOTAPTREPO_LOCATION, exist_ok=True)
        SETTINGS = {
            "local": config["host"] == "local",
            "password": config.get("repo_password"),
            "server_admin_email": config["server_admin_email"],
            "use_ssl": bool(config.get("ssl")),
            "port": config["port"],
        }
        with open(REPO_SETTINGS_LOCATION, "w") as f:
            f.write(yaml.dump(SETTINGS))
        # Copy the splash page
        if config.get("splash") is not None:
            shutil.copy(config["splash"], os.path.join(
                REPO_FILES_LOCATION, "index.html"))
        # Copy the SSL stuff
        if SETTINGS["use_ssl"]:
            shutil.copy(config["ssl"]["key"], os.path.join(
                APACHE_FILES_LOCATION, "server.key"))
            shutil.copy(config["ssl"]["cert"], os.path.join(
                APACHE_FILES_LOCATION, "server.crt"))
        try:
            # Attempt to get the GPG key from the config file
            key = config["key"]
            try:
                subprocess.check_call(
                    ["gpg", "--list-key", key], stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                if e.returncode == 2:
                    raise FileNotFoundError(
                        f"Key {key} does not exist") from None
                else:
                    raise e
        except KeyError:
            # If the GPG key is not in the config file, ask to generate one or pick one
            create_new_key = zmtools.y_to_continue(
                "Would you like to create a new GPG key to sign your DEBs?")
            if create_new_key:
                subprocess.check_call(["gpg", "--gen-key"])
            out = subprocess.check_output(
                ["gpg", "--list-keys"]).decode().strip()
            # Extract the keys using regex
            keys = [k.strip() for k in re.findall(r"(?<=]\n).+", out)]
            if create_new_key:
                # Get the created one
                key = keys[-1]
            else:
                key = zmtools.picker(keys, item_name="key")
        # Generate a random name for the public key; maybe change this in the future?
        public_key_file_name = str(uuid.uuid4()).replace("-", "")
        # Set up the repo
        subprocess.check_call(["gpg", "--armor", "--output", os.path.join(
            REPO_FILES_LOCATION, f"{public_key_file_name}.gpg.key"), "--export", key])
        os.makedirs(os.path.join(os.path.join(REPO_FILES_LOCATION, "conf")))

        with open(os.path.join(REPO_FILES_LOCATION, "conf", "distributions"), "w") as f:
            f.write(DISTRIBUTIONS_STRING.format(config["origin"], config["label"], config["codename"], " ".join(
                config["arch"]), " ".join(config["components"]), config["description"], key))
        if config["host"] != "local":
            if "private" in config["host"]:
                repo_type = "private"
            else:
                repo_type = "public"
            LOGGER.warning(
                "You are using GitHub to host your repo; your files must not exceed 100 MB and the entire repo must not exceed 100 GB")
            with zmtools.working_directory(REPO_FILES_LOCATION):
                subprocess.check_call(["git", "init"])
                subprocess.check_call(["gh", "repo", "create", NAME, f"--{repo_type}", "--description",
                                      "APT repo", "--disable-issues", "--disable-wiki", "--source=.", "--remote=origin"])
                subprocess.check_call(
                    ["git", "checkout", "-q", "-b", "gh-pages"])
                subprocess.check_call(["git", "add", "--all"])
                subprocess.check_call(
                    ["git", "commit", "-m", "set up repo", "-a"])
                subprocess.check_call(["git", "push", "origin", "gh-pages"])

    else:
        with open(os.path.join(REPO_FILES_LOCATION, "conf", "distributions"), "r") as f:
            distributions_text = f.read()

        CODENAME = re.findall(r"(?<=Codename: ).+", distributions_text)[0]
        ALL_ARCH = re.findall(r"(?<=Architectures: ).+",
                              distributions_text)[0].replace(" ", "|")

        with open(REPO_SETTINGS_LOCATION, "r") as f:
            SETTINGS = yaml.load(f, Loader=yaml.FullLoader)

        if args.command == "serve":
            container_name = f"apt-repo_{NAME}"
            if SETTINGS["local"]:
                if not args.stop:
                    environment = {
                        "SERVER_ADMIN_EMAIL": SETTINGS["server_admin_email"],
                        "USE_SSL": SETTINGS["use_ssl"]
                    }
                    if SETTINGS["password"] != "":
                        environment["REPO_PASSWORD"] = SETTINGS["password"]
                    client = docker.from_env()
                    volumes = {
                        REPO_FILES_LOCATION: {
                            "bind": os.path.join(os.sep, "usr", "local", "apache2", "htdocs"),
                            "mode": "ro"
                        },
                        APACHE_FILES_LOCATION: {
                            "bind": os.path.join(os.sep, "usr", "local", "apache2", "mounted"),
                            "mode": "rw"  # No idea why this is required, but it breaks if not read-write
                        }
                    }
                    if not SETTINGS["use_ssl"]:
                        ports = {
                            "80/tcp": SETTINGS["port"]
                        }
                    else:
                        ports = {
                            "443/tcp": SETTINGS["port"]
                        }
                    client.containers.run("apt-repo", name=container_name, auto_remove=True,
                                          detach=True, ports=ports, volumes=volumes, environment=environment)
                else:
                    client = docker.from_env()
                    client.containers.get(container_name).stop()
            else:
                raise ValueError("Cannot serve this repo locally")

        elif args.command == "add_packages":
            if not os.path.isdir(os.path.join(REPO_FILES_LOCATION, "db")):
                # First time run edge case
                original_debs_list = []
            else:
                original_debs_list = list_packages_available(
                    CODENAME, REPO_FILES_LOCATION)
            for deb_file, component, arch_ in args.deb_files:
                if os.stat(deb_file).st_size > 10000000 and not SETTINGS["local"]:
                    LOGGER.warning(
                        f"{deb_file} exceeds 100 MB; cannot add to repo")
                if arch_ == "all":
                    arch = ALL_ARCH
                else:
                    arch = arch_
                try:
                    subprocess.check_call(["reprepro", "--ask-passphrase", "-C", component,
                                          "-A", arch, "-Vb", REPO_FILES_LOCATION, "includedeb", CODENAME, deb_file])
                except subprocess.CalledProcessError as e:
                    LOGGER.exception("reprepro error")
            all_debs_list = list_packages_available(
                CODENAME, REPO_FILES_LOCATION)
            new_debs_list = [
                deb for deb in all_debs_list if deb not in original_debs_list]
            if new_debs_list:
                LOGGER.info("New DEBs added")
                print(tabulate(new_debs_list, headers="keys"))
                if not SETTINGS["local"]:
                    # Push to GitHub
                    with zmtools.working_directory(REPO_FILES_LOCATION):
                        subprocess.check_call(
                            ["git", "checkout", "-q", "gh-pages"])
                        subprocess.check_call(["git", "add", "--all"])
                        subprocess.check_call(
                            ["git", "commit", "-m", "update repo", "-a"])
                        subprocess.check_call(
                            ["git", "push", "origin", "gh-pages"])
            else:
                LOGGER.warning("No new DEBs added")

        elif args.command == "remove_packages":
            original_debs_list = list_packages_available(
                CODENAME, REPO_FILES_LOCATION)
            for package in args.packages:
                subprocess.check_call(
                    ["reprepro", "-Vb", REPO_FILES_LOCATION, "remove", CODENAME, package])
            all_debs_list = list_packages_available(
                CODENAME, REPO_FILES_LOCATION)
            removed_debs_list = [
                deb for deb in original_debs_list if deb not in all_debs_list]
            if removed_debs_list:
                LOGGER.info("DEBs removed")
                print(tabulate(removed_debs_list, headers="keys"))
                if not SETTINGS["local"]:
                    # Push to GitHub
                    with zmtools.working_directory(REPO_FILES_LOCATION):
                        subprocess.check_call(
                            ["git", "checkout", "-q", "gh-pages"])
                        subprocess.check_call(["git", "add", "--all"])
                        subprocess.check_call(
                            ["git", "commit", "-m", "update repo", "-a"])
                        subprocess.check_call(
                            ["git", "push", "origin", "gh-pages"])
            else:
                LOGGER.warning("No DEBs removed")

        elif args.command == "list_packages":
            debs = list_packages_available(CODENAME, REPO_FILES_LOCATION)
            if debs:
                if not args.no_format:
                    print(tabulate(debs, headers="keys"))
                else:
                    for deb in debs:
                        print(" ".join([v for v in deb.values()]).strip())
            else:
                LOGGER.warning(f"No DEBs in repo \"{NAME}\" yet")
        elif args.command == "clean":
            if SETTINGS["local"]:
                raise ValueError("Can only clean a repo hosted on GitHub")
            else:
                # Completely reset the entire repo
                with zmtools.working_directory(REPO_FILES_LOCATION):
                    remote = subprocess.check_output(
                        ["git", "config", "--get", "remote.origin.url"]).decode().strip()
                    shutil.rmtree(".git")
                    subprocess.check_call(["git", "init"])
                    subprocess.check_call(
                        ["git", "checkout", "-q", "-b", "gh-pages"])
                    subprocess.check_call(
                        ["git", "remote", "add", "origin", remote])
                    subprocess.check_call(["git", "add", "--all"])
                    subprocess.check_call(
                        ["git", "commit", "-m", "clean repo", "-a"])
                    subprocess.check_call(
                        ["git", "push", "origin", "gh-pages", "--force"])
        else:
            parser.print_help()
            parser.error("Invalid command")

    return 0


if __name__ == "__main__":
    sys.exit(main())
