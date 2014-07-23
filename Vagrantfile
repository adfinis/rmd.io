# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "precise64"
  config.vm.guest = :ubuntu
  config.vm.hostname = 'maildelay.vm'

  begin
    if Vagrant.plugin("2").manager.config.has_key? :vbguest then
      #config.vbguest.auto_update = false
    end
  rescue
  end

  config.vm.provider "virtualbox" do |v|
	  v.customize ['storagectl', :id, '--name', 'SATA Controller', '--hostiocache', 'on']
	  v.customize ["modifyvm", :id, "--rtcuseutc", "on"]
  end

  config.hostsupdater.remove_on_suspend = true
  #config.hostsupdater.aliases = ["timescout.vm"]

  # The url from where the 'config.vm.box' box will be fetched if it
  # doesn't already exist on the user's system.
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  #config.vm.network :forwarded_port, guest: 80, host: 8080
  #config.vm.network :forwarded_port, guest: 22, host: 2222

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network :private_network, ip: "192.168.33.21"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  config.vm.network :public_network

  # If true, then any SSH connections made will enable agent forwarding.
  # Default value: false
  config.ssh.forward_agent = true

  config.vm.provision :shell, :path => 'tools/vagrant/provision.sh'
end
