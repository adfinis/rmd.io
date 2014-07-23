
.PHONY: all config

all: help

.SUFFIXES: .po .mo

.mo.po:
	@msgfmt $< -o $@

vagrant-reset-user:
	@vagrant ssh -c "sudo su - postgres -c psql < /vagrant/tools/vagrant/user.sql > /dev/null 2>&1"
	@echo "Successfully resetted users"

vagrant-clear-log:
	@vagrant ssh -c "sudo su - postgres -c psql < /vagrant/tools/vagrant/clear-log.sql > /dev/null 2>&1"
	@echo "Successfully cleared address log"

vagrant-destroy:
	@vagrant destroy -f

vagrant-prepare:
	vagrant plugin install vagrant-hostsupdater
	vagrant up
	vagrant ssh -c 'sudo /etc/init.d/apache2 restart'
	vagrant ssh -c 'sudo /etc/init.d/mysql restart'

vagrant: vagrant-prepare vagrant-user
	@vagrant ssh -c 'cd /vagrant && bash ./tools/vagrant/showinfo.sh'

vagrant-reset: vagrant-destroy vagrant
	@echo "Vagrant reset successful"
