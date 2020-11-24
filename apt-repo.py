#! /usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess

BASE_LOCATION = os.path.join(os.sep, "opt", "apt-repo")
MOUNT_LOCATION = os.path.join(BASE_LOCATION, "mount")

os.makedirs(os.path.join(MOUNT_LOCATION, "debs_staging"), exist_ok=True)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command", help="action to take")

setup_parser = subparsers.add_parser(
    "setup", help="setup the repo for the first time")
setup_parser.add_argument("-c", "--config", default=os.path.join(
    MOUNT_LOCATION, "config.json"), type=os.path.abspath, help="config.json file location")

serve_parser = subparsers.add_parser("serve", help="start serving the repo")
serve_parser.add_argument("-p", "--port", default=8080,
                          help="port to serve repo on")
serve_parser.add_argument(
    "--stop", action="store_true", help="stop serving repo")

add_debs_parser = subparsers.add_parser(
    "add_debs", help="add DEBs to the repo")
add_debs_parser.add_argument(
    "deb_files", nargs="+", type=os.path.abspath, help="DEB files to add")
add_debs_parser.add_argument("-d", "--delete_original",
                             action="store_true", help="delete the original DEB file")

args = parser.parse_args()

os.chdir(BASE_LOCATION)

if args.command == "setup":
    with open(args.config, "r") as f:
        config = json.load(f)
    setup_command = ["./setup.sh", MOUNT_LOCATION, config["origin"], config["label"], config["codename"],
                     " ".join(config["arch"]), " ".join(config["components"]), config["description"]]
    subprocess.check_call(setup_command)
elif args.command == "serve":
    if not args.stop:
        container_id = subprocess.check_call(
            ["./serve.sh", MOUNT_LOCATION, str(args.port)], stdout=subprocess.PIPE)
        # Write this to a file
    else:
        # Read ID from a file and stop it
        raise NotImplementedError
elif args.command == "add_debs":
    if not args.delete_original:
        for deb_file in args.deb_files:
            shutil.copy(deb_file, os.path.join(MOUNT_LOCATION, "debs_staging"))
    else:
        for deb_file in args.deb_files:
            shutil.move(deb_file, os.path.join(MOUNT_LOCATION, "debs_staging"))
    subprocess.check_call(["./add_debs.sh", MOUNT_LOCATION])
else:
    raise ValueError("Invalid command")
