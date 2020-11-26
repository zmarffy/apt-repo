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
    all_arch = re.findall(r"(?<=Architectures: ).+",
                          distributions_text)[0].replace(" ", "|")
    for d in sys.argv[1:]:
        # Every argument is a DEB file
        deb_file_name, component, arch = d.split(":")
        deb_file_location = os.path.join(os.sep, "debs", deb_file_name)
        if arch == "all":
            arch = all_arch
        try:
            subprocess.run(["reprepro", "--ask-passphrase", "-C", component, "-A", arch, "-Vb",
                            ".", "includedeb", codename, deb_file_location], check=True, stdout=subprocess.PIPE)
            if arch == all_arch:
                arch = "all"
            added_debs.append((deb_file_name, component, arch))
        except subprocess.CalledProcessError as e:
            print(e)

    if added_debs:
        # Make this a pretty table or something maybe?
        s = ""
        for added_deb in added_debs:
            s += f"{added_deb[0]} ({added_deb[1]} / {added_deb[2]})\n"
        subprocess.run(["reprepro", "export"],
                       check=True, stdout=subprocess.PIPE)
        print(f"Added:\n{s.strip()}")
    else:
        print("Nothing added to repo")
except KeyboardInterrupt:
    print("DEB adding interrupted")
    sys.exit(130)
