# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "generic/ubuntu2004"
  config.vm.network "forwarded_port", guest: 80, host: 8080, host_ip: "127.0.0.1"
  config.vm.network "public_network"
  config.vm.provision "file", source: "vagrant_files/.env", destination: "~/.env", run: "always"
  config.vm.provision "file", source: "apt_repo_maker", destination: "~/src/apt_repo_maker"
  config.vm.provision "file", source: "setup.py", destination: "~/src/setup.py"
  config.vm.provision "file", source: "LICENSE", destination: "~/src/LICENSE"
  config.vm.provision "file", source: "README.md", destination: "~/src/README.md"
  config.vm.provision "shell", path: "vagrant_files/vagrant_provison.sh"
  config.vm.post_up_message = "Your virtual machine is now set up to run apt-repo-maker. If running multiple repos, forward some more ports in the Vagrantfile."
end
