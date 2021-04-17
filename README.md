# `apt-repo-maker`

`apt-repo-maker` is a program to create and host an APT repo on your server or GitHub.

## Requirements

- `docker`
- `gh`
- `gpg`

## Setup

0. This uses `install-directives` from [`zetuptools`](https://github.com/zmarffy/zetuptools). Install the `pip` package and then run `install-directives apt-repo-maker install`. Note that you must have permissions to use `docker`.

1. Run `apt-repo setup`. Usage is as follows.

    ```text
    usage: apt-repo [-h] [-n NAME] setup [-h] config
    ```

    You may select a name for your repo or leave it blank for the default, "repo". This is what allows you to serve multiple repos on one server. A YAML config file is the only required parameter. Here is an example of one.

    ```yaml
    ---
    name: zekerepo
    origin: Zeke's APT repo
    label: zeke-repo
    codename: focal
    arch:
      - amd64
      - i386
    components:
      - main
    description: Zeke's APT repo of random stuff he makes
    server_admin_email: zmarffy@yahoo.com
    host: local
    splash: .files/splash.html
    ssl:
      key: .files/host.key
      cert: .files/host.crt
    port: 443
    ```

    `splash` will set an HTML splash page for the repo. `ssl` is not a required key, but if provided, makes the repository use HTTPS. Duh. You can set a repo password with the key `repo_password`. This will enable basic authentication for the repo. The username is "repo".

    Any key that requires a file location (such as `splash`) uses the location relative to where you are running `apt-repo` from, NOT relative to the config file.

    Using "`github`" or "`github-private`" as `host` will create a repo on GitHub to host your APT repo in. Yes, this is weird. Yes, it works.

    **Note:** Do not specify "`all`" as an architecture here, even if you have packages that fit all architectures.

2. Add some DEB files to the repo.

    ```text
    apt-repo [-h] [-n NAME] add_packages [-h] [-d] deb_files [deb_files ...]
    ```

    **Note:** You can specify DEB files with just their filenames, or like "`[location]:[component]`"; for example: "`mydeb_1.0.0-1_all.deb:main`". Architecture will be determined automatically (by reading packages' actual architecture fields; not by assuming from their names).

3. Serve the repo.

    ```text
    apt-repo [-h] [-n NAME] serve [-h] [-s]
    ```

    The `-s` flag stops the repo from being served. The port it is served on is specified in the config file when you first set it up.

**Note**: Before you uninstall this package, you should run `install-directives apt-repo-maker uninstall` to stop any served repos as well as delete the created Docker images.

## Other stuff you can do

- List the packages in the repo

    ```text
    apt-repo [-h] [-n NAME] list_packages [-h] [--no_format]
    ```

- Remove packages in the repo

    ```text
    apt-repo [-h] [-n NAME] remove_packages [-h] packages [packages ...]
    ```

- Getting low on space on a GitHub-hosted repo? Run the clean function

    ```text
    apt-repo [-h] [-n NAME] clean [-h]
    ```

## Tips

- Why not host your repo on an Amazon S3 bucket? Mount it to your computer using [`s3fs`](http://manpages.ubuntu.com/manpages/xenial/man1/s3fs.1.html)

## How can users add created repos to their APT sources if I use GitHub as the host

This is largely a question about APT, not something for this project specifically, but I'll lend a hand.

If your GitHub repo is private, tell those who need access to it to generate a personal access token with repo read abilities (you can do so [in the web interface](https://github.com/settings/tokens/new), or even use [a Selenium script](https://gist.github.com/zmarffy/11eee870c73d6a25d49bacc06b24a8ab)). Then they should add the following to their `/etc/apt/sources.list`.

```text
deb https://[username]:[personal_access_token]@raw.githubusercontent.com/[repo_host_username]/[repo_name]/gh-pages [codename] [component]
```

If your GitHub repo is public, the same method can be followed (`[username]:[password]` is not necessary though), or you can use this much nicer form.

```text
deb https://[repo_host_username].github.io/[repo_name]/ [codename] [component]
```

That's the whole point of GitHub pages, after all, that "nicer form".
