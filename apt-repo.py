#! /usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys
import zmtools

BASE_LOCATION = os.path.join(os.sep, "opt", "apt-repo")
# Parameterize this for hosting multiple repos
MOUNT_LOCATION = os.path.join(BASE_LOCATION, "mount")


def _deb_file_transform(s):
    d = s.rsplit(".deb:", 1)
    try:
        c = d[1]
        f = os.path.abspath(d[0] + ".deb")
    except IndexError:
        c = None
        f = os.path.abspath(d[0])
    return f, c


def wipe_all_if_necessary(mount_location):
    if os.listdir(mount_location):
        if zmtools.y_to_continue(f"Repo already set up at {mount_location}; wipe and start over? (y/n)") and zmtools.y_to_continue("Are you REALLY sure you want to wipe the repo? There is no going back from this. (y/n)"):
            shutil.rmtree(mount_location)
            os.mkdir(mount_location)
        else:
            sys.exit("Setup aborted")


def stage_debs(deb_files, delete_original):
    if delete_original:
        f = shutil.move
    else:
        f = shutil.copy
    for deb_file, component in deb_files:
        try:
            fn = deb_file.rsplit(os.sep, 1)[1]
        except IndexError:
            fn = deb_file
        if component is None:
            component = input(f"{deb_file} component: ")
        f(deb_file, os.path.join(MOUNT_LOCATION, "debs_staging", component, fn))


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
    "deb_files", nargs="+", type=_deb_file_transform, help="DEB files to add")
add_debs_parser.add_argument("-d", "--delete_original",
                             action="store_true", help="delete the original DEB file")

args = parser.parse_args()

os.chdir(BASE_LOCATION)

if os.geteuid() != 0:
    print("WARNING: You may want to run this as root")

if args.command == "setup":
    wipe_all_if_necessary(MOUNT_LOCATION)
    with open(args.config, "r") as f:
        config = json.load(f)
    for component in config["components"]:
        os.makedirs(os.path.join(MOUNT_LOCATION,
                                 "debs_staging", component), exist_ok=True)
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
    stage_debs(args.deb_files, args.delete_original)
    subprocess.check_call(["./add_debs.sh", MOUNT_LOCATION])
else:
    raise parser.error("Invalid command")
