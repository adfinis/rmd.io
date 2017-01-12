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

docker-start:
	docker-compose start

docker-stop:
	docker-compose stop

docker-init:
	docker-compose up -d

docker-db-init:
	psql -h 127.0.0.1 -U rmdio -d maildelay -f tools/vagrant/database.sql
	python app/manage.py syncdb --noinput
	python app/manage.py migrate

restart-apache:
	@vagrant ssh -c "sudo service apache2 restart"

css:
	@cd app/static; make css

watch:
	@cd app/static; make watch
