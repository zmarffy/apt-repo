# `apt-repo`

`apt-repo` is a program to create and host an APT repo on your server or GitHub.

## Requirements

- `docker`
- `gh`
- `gpg`
- `python3`
- `python-magic` (a `pip` package)
- `pyyaml` (a `pip` package)
- `zmtools` (a `pip` package)

## Setup

1. Run `apt-repo setup`. Usage is as follows.

    ```text
    usage: apt-repo [-h] [-n NAME] [-l BASE_LOCATION] setup [-h] [--splash SPLASH] config
    ```

    You may select a name for your repo or leave it blank for the default, "repo". This is what allows you to serve multiple repos on one server. You may also add an HTML splash page if you'd like. A JSON or YAML config file is the only required parameter, though. Here is an example of one.

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
        "description": "Zeke's APT repo of random stuff he makes",
        "host": "local"
    }
    ```

    Using "`github`" or "`github-private`" as "`host`" will create a repo on GitHub to host your APT repo in. Yes, this is weird. Yes, it works.

    **Note:** Do not specify "`all`" as an architecture here, even if you have packages that fit all architectures.

2. Add some DEB files to the repo.

    ```text
    apt-repo [-h] [-n NAME] [-l BASE_LOCATION] add_packages [-h] [-d] deb_files [deb_files ...]
    ```

    **Note:** You can specify DEB files with just their filenames, or like "`[location]:[component]`"; for example: "`mydeb_1.0.0-1_all.deb:main`". Architecture will be determined automatically (by reading packages' actual architecture fields; not by assuming from their names).

3. Serve the repo.

    ```text
    apt-repo [-h] [-n NAME] [-l BASE_LOCATION] serve [-h] [-p PORT] [-s]
    ```

    The `-s` flag stops the repo from being served.

## Other stuff you can do

- List the packages in the repo

    ```text
    apt-repo [-h] [-n NAME] [-l BASE_LOCATION] list [-h] [--pretty]
    ```

- Remove packages in the repo

    ```text
    apt-repo [-h] [-n NAME] [-l BASE_LOCATION] remove_packages [-h] packages [packages ...]
    ```

## Tips

- Why not host your repo on an Amazon S3 bucket? Mount it to your computer using [`s3fs`](http://manpages.ubuntu.com/manpages/xenial/man1/s3fs.1.html). You can even [enable auth](https://stackoverflow.com/questions/3091084/does-amazon-s3-support-http-request-with-basic-authentication) if you do that

## How can users add created repos to their APT sources if I use GitHub as the host

This is largely a question about APT, not something for this project specifically, but I'll lend a hand.

If your GitHub repo is private, tell those who need access to it to generate a personal access token with repo read abilities (you can do so [in the web interface](https://github.com/settings/tokens/new), or even use [a Selenium script](https://gist.github.com/zmarffy/11eee870c73d6a25d49bacc06b24a8ab)). Then they should add the following to their `/etc/apt/sources.list`.

`deb https://[username]:[personal_access_token]@raw.githubusercontent.com/[repo_host_username]/[repo_name]/gh-pages [component]`

If your GitHub repo is public, the same method can be followed (`[username]:[password]` is not necessary though), or you can use this much nicer form.

`deb https://[repo_host_username].github.io/[repo_name]/ focal main`

That's the whole point of GitHub pages, after all, that "nicer form".

## Missing features

- HTTPS and auth for local repos
- Renewing one's GPG key/switching which key the repo is signed with
