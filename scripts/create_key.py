import os
import subprocess
import sys
import uuid

try:
    subprocess.run(["gpg", "--gen-key"])
    out = subprocess.run(["gpg", "--list-key"],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    id_ = out.split("\n")[3].strip()
    key_name = str(uuid.uuid4()).replace("-", "")
    subprocess.run(["gpg", "--armor", "--output", os.path.join(os.sep,
                                                               "share", f"{key_name}.gpg.key"), "--export", id_], check=True)
except KeyboardInterrupt:
    print("Key creation interrupted")
    sys.exit(130)
