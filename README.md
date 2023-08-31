# `apt-repo-maker`

`apt-repo-maker` is a program to create and host an APT repo on GitHub. Yes, this means committing binaries to a repo, because why not. It wraps `reprepro` with a very simple CLI.

## Setup

Run `apt-repo setup`. Usage is as follows.

```text
usage: apt-repo setup [-h] --public-key PUBLIC_KEY --private-key PRIVATE_KEY --description DESCRIPTION --origin ORIGIN --label LABEL --codename CODENAME --arch ARCH [ARCH ...] --component
                      COMPONENT [COMPONENT ...] [--splash SPLASH] [--private]
                      name

positional arguments:
  name

options:
  -h, --help            show this help message and exit
  --public-key PUBLIC_KEY
                        public key to copy to repo
  --private-key PRIVATE_KEY
                        private key to sign packages with
  --description DESCRIPTION
  --origin ORIGIN
  --label LABEL
  --codename CODENAME
  --arch ARCH [ARCH ...]
  --component COMPONENT [COMPONENT ...]
  --splash SPLASH       HTML splash page for the repo
  --private             make repo private
```

All of the parameters are required and are fairly self-explanatory. The public key should be an exported file and the private key should be the private key ID in GPG.

Add some DEB files to the repo.

```text
usage: apt-repo add [-h] name debs [debs ...]

positional arguments:
  name
  debs        DEB files to add (either just their locations, or <location>:<component>)

options:
  -h, --help  show this help message and exit
```

**Note:** You can specify DEB files with just their filenames, or like `<location>:<component>`; for example: `mydeb_1.0.0-1_all.deb:main`. Architecture will be determined automatically (by reading packages' actual architecture fields; not by assuming from their names).

## Other stuff you can do

- List the packages in the repo

    ```text
    usage: apt-repo list [-h] [--no-format] name

    positional arguments:
    name

    options:
    -h, --help   show this help message and exit
    --no-format  do not pretty-print list
    ```

- Remove packages in the repo

    ```text
    usage: apt-repo remove [-h] name packages [packages ...]

    positional arguments:
    name
    packages    packages to remove

    options:
    -h, --help  show this help message and exit
    ```

- Getting low on space on the GitHub repo? Run the clean function

    ```text
    usage: apt-repo clean [-h] name

    positional arguments:
    name

    options:
    -h, --help  show this help message and exit
    ```

## How can users add my created repos to their APT sources

This is largely a question about APT, not something for this project specifically, but I'll lend a hand.

If your GitHub repo is private, tell those who need access to it to generate a personal access token with repo read abilities (you can do so [in the web interface](https://github.com/settings/tokens/new), or even use [a Selenium script](https://gist.github.com/zmarffy/11eee870c73d6a25d49bacc06b24a8ab)). Then they should add the following to their `/etc/apt/sources.list`.

```text
deb https://<username>:<personal_access_token>@raw.githubusercontent.com/<repo_host_username>/<repo_name>/gh-pages <codename> <component>
```

If your GitHub repo is public, the same method can be followed (`<username>:<password>` is not necessary though), or you can use this much nicer form.

```text
deb https://<repo_host_username>.github.io/<repo_name>/ <codename> <component>
```

That's the whole point of GitHub pages, after all, that "nicer form".

## Limitations

- Files on stored GitHub can be no greater than 100 MB. This poses a significant issue for hosting APT repos, as 100 MB packages aren't too uncommon. Consider breaking your package up into multiple parts that are dependent on each other if you need to upload a package greater than 100 MB
