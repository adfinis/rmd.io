.PHONY: all config

.SUFFIXES: .po .mo

.mo.po:
	@msgfmt $< -o $@

init-user:
	@vagrant ssh -c "sudo su - postgres -c psql < /vagrant/tools/vagrant/user.sql > /dev/null 2>&1"
	@echo "Successfully resetted users"

import:
	vagrant ssh -c "/vagrant/envpy /vagrant/app/manage.py import"

sendmail:
	vagrant ssh -c "/vagrant/envpy /vagrant/app/manage.py sendmail"

clear-address-log:
	@vagrant ssh -c "sudo su - postgres -c psql < /vagrant/tools/vagrant/clear-log.sql > /dev/null 2>&1"
	@echo "Successfully cleared address log"

vagrant-destroy:
	@vagrant destroy -f

vagrant-prepare:
	@vagrant plugin install vagrant-hostsupdater
	@vagrant up
	@vagrant ssh -c 'sudo /etc/init.d/apache2 restart'

vagrant: vagrant-prepare init-user
	@vagrant ssh -c 'cd /vagrant && bash ./tools/vagrant/showinfo.sh'

vagrant-reset: vagrant-destroy vagrant
	@echo "Vagrant reset successful"

migrate:
	@vagrant ssh -c "/vagrant/envpy /vagrant/app/manage.py schemamigration mails --auto"
	@vagrant ssh -c "/vagrant/envpy /vagrant/app/manage.py migrate mails"
	@echo "Successfully migrated DB structure"

restart-apache:
	@vagrant ssh -c "sudo service apache2 restart"

css:
	@cd app/static; make css

watch:
	@cd app/static; make watch
