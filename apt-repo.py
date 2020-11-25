#! /usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys

import zmtools


def determine_arch(deb_file):
    if os.path.isfile("determine_arch.sh"):
        # You know I had to do it to 'em ("it" == "copy and paste code from SO and not be bothered to write it in another language")
        return subprocess.check_output(["./determine_arch.sh", deb_file]).decode().strip()


def _deb_file_transform(s):
    d = s.split(".deb:")
    if len(d) != 1:
        d1 = d[1].split(":")
        c = d1[0]
        if c == "":
            c = None
        a = d1[1]
        if a == "":
            a = None
        f = os.path.abspath(d[0] + ".deb")
    else:
        c = None
        a = None
        f = os.path.abspath(s)
    if a is None:
        a = determine_arch(f)
    return f, c, a


def wipe_all_if_necessary(mount_location, dotrepos_location):
    try:
        setup_already = bool(os.listdir(mount_location))
    except FileNotFoundError:
        setup_already = False
    if setup_already:
        if zmtools.y_to_continue(f"Repo already set up at {mount_location}; wipe and start over? (y/n)") and zmtools.y_to_continue("Are you REALLY sure you want to wipe the repo? There is no going back from this. (y/n)"):
            shutil.rmtree(mount_location)
            os.mkdir(mount_location)
            shutil.rmtree(dotrepos_location)
            os.makedirs(dotrepos_location)
        else:
            sys.exit("Setup aborted")
    else:
        os.makedirs(mount_location, exist_ok=True)
        os.makedirs(dotrepos_location, exist_ok=True)


def stage_debs(mount_location, deb_files, delete_original):
    # Wow, this is wacky!
    if delete_original:
        f = shutil.move
    else:
        f = shutil.copy
    for deb_file, component, arch in deb_files:
        try:
            fn = deb_file.rsplit(os.sep, 1)[1]
        except IndexError:
            fn = deb_file
        if component is None:
            component = input(f"{deb_file} component: ")
            if component == "":
                raise ValueError("Empty component")
        if arch is None:
            arch = input(f"{deb_file} architecture: ")
            if arch == "":
                # Impossible?
                raise ValueError("Empty architecture")
        folders = os.path.join(mount_location, "debs_staging", component, arch)
        os.makedirs(folders, exist_ok=True)
        f(deb_file, os.path.join(folders, fn))


parser = argparse.ArgumentParser()

parser.add_argument("-n", "--name", default="repo",
                    help="repo name (where to mount files for repo)")

subparsers = parser.add_subparsers(dest="command", help="action to take")

setup_parser = subparsers.add_parser(
    "setup", help="setup the repo for the first time")
setup_parser.add_argument("config", type=os.path.abspath,
                          help="config.json file location")
setup_parser.add_argument("--splash", type=os.path.abspath,
                          help="HTML splash page location")

serve_parser = subparsers.add_parser("serve", help="start serving the repo")
serve_parser.add_argument("-p", "--port", default=8080,
                          help="port to serve repo on")
serve_parser.add_argument(
    "-s", "--stop", action="store_true", help="stop serving repo")

add_debs_parser = subparsers.add_parser(
    "add_debs", help="add DEBs to the repo")
add_debs_parser.add_argument("deb_files", nargs="+", type=_deb_file_transform,
                             help="DEB files to add (either just their locations, or [location]:[component]:[architecture])")
add_debs_parser.add_argument("-d", "--delete_original",
                             action="store_true", help="delete the original DEB file")

args = parser.parse_args()

NAME = args.name
BASE_SCRIPTS_LOCATION = os.path.join(os.sep, "usr", "share", "apt-repo")
BASE_LOCATION = os.path.join(os.sep, "opt", "apt-repo")
MOUNT_LOCATION = os.path.join(BASE_LOCATION, NAME)
GPG_MOUNT_LOCATION = os.path.join(BASE_LOCATION, "gpg")
DOTREPOS_LOCATION = os.path.join(BASE_LOCATION, ".repos", NAME)

os.chdir(BASE_SCRIPTS_LOCATION)

if os.geteuid() != 0:
    print("WARNING: You may want to run this as root")

if args.command == "setup":
    with open(args.config, "r") as f:
        config = json.load(f)
    wipe_all_if_necessary(MOUNT_LOCATION, DOTREPOS_LOCATION)
    if args.splash is not None:
        shutil.copy(args.splash, os.path.join(
            MOUNT_LOCATION, "repo_files", "index.html"))
    setup_command = ["./setup.sh", MOUNT_LOCATION, GPG_MOUNT_LOCATION, config["origin"], config["label"],
                     config["codename"], " ".join(config["arch"]), " ".join(config["components"]), config["description"]]
    subprocess.check_call(setup_command)
elif args.command == "serve":
    if not args.stop:
        container_id = subprocess.check_output(
            ["./serve.sh", MOUNT_LOCATION, str(args.port), NAME]).decode().strip()
        with open(os.path.join(DOTREPOS_LOCATION, "containerid"), "w") as f:
            f.write(container_id)
    else:
        with open(os.path.join(DOTREPOS_LOCATION, "containerid"), "r") as f:
            container_id = f.read().strip()
            subprocess.check_call(
                ["docker", "container", "stop", container_id], stdout=subprocess.PIPE)
elif args.command == "add_debs":
    try:
        stage_debs(MOUNT_LOCATION, args.deb_files, args.delete_original)
        subprocess.check_call(
            ["./add_debs.sh", MOUNT_LOCATION, GPG_MOUNT_LOCATION])
    finally:
        # Cleanup staging folder
        shutil.rmtree(os.path.join(MOUNT_LOCATION, "debs_staging"))
        os.mkdir(os.path.join(MOUNT_LOCATION, "debs_staging"))
# Need to add removal
else:
    raise parser.error("Invalid command")
