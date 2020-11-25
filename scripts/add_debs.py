import os
import re
import shutil
import subprocess
import sys

os.chdir(os.path.join(os.sep, "share"))

added_debs = []

try:
    with open(os.path.join(os.sep, "share", "conf", "distributions"), "r") as f:
        distributions_text = f.read()
    codename = re.findall(r"(?<=Codename: ).+", distributions_text)[0]
    all_arch = re.findall(r"(?<=Architectures: ).+", distributions_text)[0].replace(" ", "|")
    for deb_file in os.listdir(os.path.join(os.sep, "debs")):
        deb_file_location, component, arch = os.path.join(os.sep, "debs", deb_file).split(":")
        shutil.move(os.path.join(os.sep, "debs", deb_file), deb_file_location)
        if arch == "all":
            arch = all_arch
        try:
            subprocess.run(["reprepro", "--ask-passphrase", "-C", component, "-A", arch, "-Vb",
                            ".", "includedeb", codename, deb_file_location], check=True, stdout=subprocess.PIPE)
            if arch == all_arch:
                arch = "all"
            added_debs.append((deb_file_location, component, arch))
            os.remove(deb_file_location)
        except subprocess.CalledProcessError as e:
            print(e)

    if added_debs:
        # Make this a pretty table or something maybe?
        s = ""
        for added_deb in added_debs:
            s += f"{added_deb[0]} ({added_deb[1]} / {added_deb[2]})\n"
        subprocess.run(["reprepro", "export"],
                       check=True, stdout=subprocess.PIPE)
        print(f"Added:\n{s}")
    else:
        print("Nothing added to repo")
except KeyboardInterrupt:
    print("DEB adding interrupted")
    sys.exit(130)
