#! /bin/bash

user='vagrant'

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo add-apt-repository ppa:deadsnakes/ppa
apt-get update
apt-get install -y \
    build-essential \
    reprepro \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    gh
python3.10 -m ensurepip
echo -e "set -a; . /home/$user/.env; set +a" > "/etc/profile.d/loadenvvars.sh"
bash /etc/profile.d/loadenvvars.sh
su - $user -c 'gh auth setup-git'
sudo usermod -aG docker $user
python3.10 -m pip install "/home/$user/src"
su - $user -c 'python3.10 -m zetuptools apt-repo-maker install'