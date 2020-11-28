#! /usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid

import magic
from reequirements import Requirement
from tabulate import tabulate
import yaml
import zmtools

LIST_OUTPUT_KEYS = ("codename", "component", "arch", "name", "version")


REQUIREMENTS = [
    Requirement("docker", ["docker", "-v"]),
    Requirement("reprepro", ["reprepro", "--version"]),
    Requirement("gpg", ["gpg", "--version"])
]

for requirement in REQUIREMENTS:
    requirement.check()


def main():

    def list_debs_available(codename, repo_files_location):
        return [dict(zip(LIST_OUTPUT_KEYS, p)) for p in [b[0].split("|") + b[1].split(" ", 1) for b in [d0.split(": ", 1) for d0 in subprocess.check_output(["reprepro", "-b", repo_files_location, "list", codename]).decode().strip().split("\n")]]]

    def determine_arch(deb_file):
        out = subprocess.check_output(["dpkg", "--info", deb_file]).decode()
        return re.findall("(?<=Architecture: ).+", out)[0]

    def _deb_file_transform(s):
        d = s.split(".deb:")
        if len(d) != 1:
            if ":" not in d[1]:
                add_debs_parser.print_help()
                add_debs_parser.error(
                    f"Incorrect format for input \"{s}\" (use just its location, or [location]:[component]:[architecture])")
            d1 = d[1].split(":")
            c = d1[0]
            if c == "":
                c = None
            a = d1[1]
            if a == "":
                a = None
            f = d[0] + ".deb"
        else:
            c = None
            a = None
            f = s
        if a is None:
            a = determine_arch(f)
        if c is None:
            c = input(f"{f} component: ")
            if c == "":
                raise ValueError("Empty component")
        if a is None:
            # Impossible?
            a = input(f"{f} architecture: ")
            if a == "":
                raise ValueError("Empty architecture")
        return f, c, a

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n", "--name", help="repo name (overridden by config's \"name\" key)")

    subparsers = parser.add_subparsers(dest="command", help="action to take")

    setup_parser = subparsers.add_parser(
        "setup", help="setup the repo for the first time")
    setup_parser.add_argument("config", type=os.path.abspath,
                              help="config.json file location")
    setup_parser.add_argument("--splash", type=os.path.abspath,
                              help="HTML splash page location")

    serve_parser = subparsers.add_parser(
        "serve", help="start serving the repo")
    serve_parser.add_argument("-p", "--port", default=8080,
                              help="port to serve repo on")
    serve_parser.add_argument(
        "-s", "--stop", action="store_true", help="stop serving repo")

    add_debs_parser = subparsers.add_parser(
        "add_debs", help="add DEBs to the repo")
    add_debs_parser.add_argument("deb_files", nargs="+", type=_deb_file_transform,
                                 help="DEB files to add (either just their locations, or [location]:[component]:[architecture])")

    list_debs_parser = subparsers.add_parser(
        "list_debs", help="list DEBs in the repo")
    list_debs_parser.add_argument(
        "--pretty", action="store_true", help="pretty-print")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        parser.error("Need to specify a command")

    NAME = args.name
    name_from_config = False
    if args.command == "setup":
        with open(args.config, "r") as f:
            if magic.from_file(args.config).endswith("json"):
                config = json.load(f)
            else:
                # Why not?
                config = yaml.load(f, Loader=yaml.FullLoader)
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
        # If only using one repo, use that as NAME
        files = os.listdir(BASE_LOCATION)
        files.remove(".repos")
        if len(files) == 1:
            NAME = files[0]

    REPO_LOCATION = os.path.join(BASE_LOCATION, NAME)
    REPO_FILES_LOCATION = os.path.join(REPO_LOCATION, "repo_files")
    DOTREPOS_LOCATION = os.path.join(BASE_LOCATION, ".repos", NAME)

    if args.command != "setup":
        with open(os.path.join(REPO_FILES_LOCATION, "conf", "distributions"), "r") as f:
            distributions_text = f.read()

        CODENAME = re.findall(r"(?<=Codename: ).+", distributions_text)[0]
        ALL_ARCH = re.findall(r"(?<=Architectures: ).+",
                            distributions_text)[0].replace(" ", "|")

    if args.command == "setup":
        # Completely wipe the repo if the user wants to
        try:
            setup_already = bool(os.listdir(REPO_LOCATION))
        except FileNotFoundError:
            setup_already = False
        if setup_already:
            if zmtools.y_to_continue(f"Repo already set up at {REPO_LOCATION}; wipe and start over? (y/n)") and zmtools.y_to_continue("Are you REALLY sure you want to wipe the repo? There is no going back from this. (y/n)"):
                shutil.rmtree(REPO_LOCATION)
                shutil.rmtree(DOTREPOS_LOCATION)
            else:
                sys.exit("Setup aborted")
        # Make necessary directories if necessary
        os.makedirs(REPO_LOCATION, exist_ok=True)
        os.makedirs(REPO_FILES_LOCATION, exist_ok=True)
        os.makedirs(DOTREPOS_LOCATION, exist_ok=True)
        # Copy the splash page
        if args.splash is not None:
            shutil.copy(args.splash, os.path.join(
                REPO_FILES_LOCATION, "index.html"))
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
        distributions_string = """Origin: {}
Label: {}
Codename: {}
Architectures: {}
Components: {}
Description: {}
SignWith: {}
"""
        with open(os.path.join(REPO_FILES_LOCATION, "conf", "distributions"), "w") as f:
            f.write(distributions_string.format(config["origin"], config["label"], config["codename"], " ".join(
                config["arch"]), " ".join(config["components"]), config["description"], key))

    elif args.command == "serve":
        if not args.stop:
            container_id = subprocess.check_output(
                ["docker", "run", "--rm", "-d", "--name", f"apt-repo_{NAME}", "-p", f"{args.port}:80", "-v", f"{REPO_FILES_LOCATION}:{os.path.join(os.sep, 'usr', 'local', 'apache2', 'htdocs')}", "httpd"]).decode().strip()
            with open(os.path.join(DOTREPOS_LOCATION, "containerid"), "w") as f:
                f.write(container_id)
        else:
            with open(os.path.join(DOTREPOS_LOCATION, "containerid"), "r") as f:
                container_id = f.read().strip()
                subprocess.check_output(
                    ["docker", "container", "stop", container_id])

    elif args.command == "add_debs":
        if not os.path.isdir(os.path.join(REPO_FILES_LOCATION, "db")):
            # First time run edge case
            original_debs_list = []
        else:
            original_debs_list = list_debs_available(
                CODENAME, REPO_FILES_LOCATION)
        for deb_file, component, arch in args.deb_files:
            if arch == "all":
                arch = ALL_ARCH
            try:
                subprocess.check_call(["reprepro", "--ask-passphrase", "-C", component,
                                       "-A", arch, "-Vb", REPO_FILES_LOCATION, "includedeb", CODENAME, deb_file])
                if arch == ALL_ARCH:
                    arch = "all"
            except subprocess.CalledProcessError as e:
                print(e)
        all_debs_list = list_debs_available(CODENAME, REPO_FILES_LOCATION)
        new_debs_list = [
            deb for deb in all_debs_list if deb not in original_debs_list]
        if new_debs_list:
            print()
            print("New DEBs added")
            print(tabulate(new_debs_list, headers="keys"))
        else:
            print("No new DEBs added")

    elif args.command == "remove_debs":
        # Need to add removal
        raise NotImplementedError()

    elif args.command == "list_debs":
        debs = list_debs_available(CODENAME, REPO_FILES_LOCATION)
        if args.pretty:
            print(tabulate(debs, headers="keys"))
        else:
            for deb in debs:
                print(" ".join([v for v in deb.values()]).strip())

    else:
        parser.print_help()
        parser.error("Invalid command")
    return 0


if __name__ == "__main__":
    sys.exit(main())
