import os
import subprocess
import sys

DISTRIBUTIONS_STRING = """Origin: {}
Label: {}
Codename: {}
Architectures: {}
Components: {}
Description: {}
SignWith: {}
"""

try:
    out = subprocess.run(["gpg", "--list-key"],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    id_ = out.split("\n")[3].strip()
    os.makedirs(os.path.join(os.sep, "share", "conf"))
    with open(os.path.join(os.sep, "share", "conf", "distributions"), "w") as f:
        f.write(DISTRIBUTIONS_STRING.format(os.environ["origin"], os.environ["label"], os.environ["codename"],
                                            os.environ["arch"], os.environ["components"], os.environ["description"], id_))
except KeyboardInterrupt:
    print("Repo configuration interrupted")
    sys.exit(130)
