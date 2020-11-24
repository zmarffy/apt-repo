import os
import re
import subprocess
import sys

os.chdir(os.path.join(os.sep, "share"))

added_debs = []

try:
    with open(os.path.join(os.sep, "share", "conf", "distributions"), "r") as f:
        codename = re.findall(r"(?<=Codename: ).+", f.read())[0]
    for component in os.listdir(os.path.join(os.sep, "debs")):
        for deb_file in os.listdir(os.path.join(os.sep, "debs", component)):
            deb_file_location = os.path.join(os.sep, "debs", component, deb_file)
            try:
                subprocess.run(["reprepro", "--ask-passphrase", "-C", component, "-Vb", ".", "includedeb", codename, deb_file_location], check=True, stdout=subprocess.PIPE)
                added_debs.append((deb_file, component))
                os.remove(deb_file_location)
            except subprocess.CalledProcessError as e:
                print(e)

    if added_debs:
        s = ""
        for added_deb in added_debs:
            s += f"{added_deb[0]} ({added_deb[1]})\n"
        subprocess.run(["reprepro", "export"],
                       check=True, stdout=subprocess.PIPE)
        print(f"Added:\n{s}")
    else:
        print("Nothing added")
except KeyboardInterrupt:
    print("DEB adding interrupted")
    sys.exit(130)
