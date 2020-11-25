import os
import re
import subprocess
import sys

os.chdir(os.path.join(os.sep, "share"))

added_debs = []

try:
    with open(os.path.join(os.sep, "share", "conf", "distributions"), "r") as f:
        distributions_text = f.read()
    codename = re.findall(r"(?<=Codename: ).+", distributions_text)[0]
    all_arch = re.findall(r"(?<=Architectures: ).+", distributions_text)[0].replace(" ", "|")
    for component in os.listdir(os.path.join(os.sep, "debs")):
        for arch in os.listdir(os.path.join(os.sep, "debs", component)):
            for deb_file in os.listdir(os.path.join(os.sep, "debs", component, arch)):
                deb_file_location = os.path.join(
                    os.sep, "debs", component, arch, deb_file)
                if arch == "all":
                    arch = all_arch
                try:
                    subprocess.run(["reprepro", "--ask-passphrase", "-C", component, "-A", arch, "-Vb",
                                    ".", "includedeb", codename, deb_file_location], check=True, stdout=subprocess.PIPE)
                    if arch == all_arch:
                        arch = "all"
                    added_debs.append((deb_file, component, arch))
                    os.remove(deb_file_location)
                except subprocess.CalledProcessError as e:
                    print(e)

    if added_debs:
        s = ""
        for added_deb in added_debs:
            s += f"{added_deb[0]} ({added_deb[1]} / {added_deb[2]})\n"
        subprocess.run(["reprepro", "export"],
                       check=True, stdout=subprocess.PIPE)
        print(f"Added:\n{s}")
    else:
        print("Nothing added")
except KeyboardInterrupt:
    print("DEB adding interrupted")
    sys.exit(130)
