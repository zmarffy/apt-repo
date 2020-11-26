# `apt-repo`

`apt-repo` very oddly-structured program to create and host a repo on your computer. It was originally structured like this to keep things as as dependency-free as possible, as Docker is used for the main functionailty. This should be built and installed with [`debpacker`](https://github.com/zmarffy/debpacker).

## Requirements

- `docker`
- `python3`
- `zmtools` (a `pip` package)

## Setup

1. Install the DEB package
2. Run `apt-repo setup`. Usage is as follows.

    ```text
    usage: apt-repo [-h] [-n NAME] setup [-h] [--splash SPLASH] config
    ```

    You may select a name for your repo or leave it blank for the default, "repo". This is what allows you to serve multiple repos on one server. You may also add an HTML splash page if you'd like. A config file is the only required parameter, though. Here is an example of one.

    ```json
    {
        "origin": "Zeke's APT repo",
        "label": "zeke-repo",
        "codename": "focal",
        "arch": [
            "amd64"
        ],
        "components": [
            "main"
        ],
        "description": "Zeke's APT repo of random stuff he makes"
    }
    ```

    *Note: Do not specify "`all`" as an architecture here, even if you have packages that fit all architectures.*

3. Add some DEB files to the repo.

    ```text
    apt-repo [-h] [-n NAME] add_debs [-h] [-d] deb_files [deb_files ...]
    ```

    *Note: You can specify DEB files with just their filenames, or like "`[location]:[component]:[architecture]`"; for example: "`mydeb_1.0.0-1_all.deb:main:all`". You can specify just one of the variables so long as you have both colons. Architecture will be determined automatically if you do not specify it (by reading packages' actual architecture fields; not by assuming from their names).*

4. Serve the repo.

    ```text
    apt-repo [-h] [-n NAME] serve [-h] [-p PORT] [-s]
    ```

    The `-s` flag stops the repo from being served.

## Missing features

- HTTPS and auth
- Listing DEBs
- Removing DEBs
- Renewing one's GPG key