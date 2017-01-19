.PHONY: import sendmail migrate start docker-start docker-stop docker-init docker-db-init css watch

import:
	@python app/manage.py import

sendmail:
	@python app/manage.py sendmail

migrate:
	@python app/manage.py migrate

start: docker-start
	@python app/manage.py runserver

docker-start:
	@docker-compose start

docker-stop:
	@docker-compose stop

docker-init:
	@docker-compose up -d

docker-db-init:
	@psql -h 127.0.0.1 -U rmdio -d maildelay -f tools/vagrant/database.sql
	@python app/manage.py syncdb --noinput
	@python app/manage.py migrate

css:
	@cd app/static; make css

watch:
	@cd app/static; make watch
