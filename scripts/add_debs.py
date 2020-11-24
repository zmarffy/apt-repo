import os
import subprocess
import sys

os.chdir(os.path.join(os.sep, "share"))

added_debs = []

try:
    for deb_file in os.listdir(os.path.join(os.sep, "debs")):
        deb_file_location = os.path.join(os.sep, "debs", deb_file)
        codename = input(f"{deb_file} codename: ")
        try:
            subprocess.run(["reprepro", "--ask-passphrase", "-Vb", ".", "includedeb",
                            codename, deb_file_location], check=True, stdout=subprocess.PIPE)
            added_debs.append(deb_file)
            os.remove(deb_file_location)
        except subprocess.CalledProcessError as e:
            print(e)

    s = "\n".join(added_debs)
    if added_debs:
        subprocess.run(["reprepro", "export"],
                       check=True, stdout=subprocess.PIPE)
        print(f"Added:\n{s}")
    else:
        print("Nothing added")
except KeyboardInterrupt:
    print("DEB adding interrupted")
    sys.exit(130)
