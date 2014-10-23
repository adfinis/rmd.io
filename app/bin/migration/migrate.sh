#!/bin/bash

pg_dump -t mails_identity maildelay_old | psql maildelay
pg_dump -t django_content_type maildelay_old | psql maildelay

# delete all auth and django tables
psql maildelay < /vagrant/app/bin/migration/preparation.sql

# take them from the old db and insert into the new
pg_dump -t auth_user maildelay_old | psql maildelay
pg_dump -t auth_group maildelay_old | psql maildelay
pg_dump -t auth_group_permissions maildelay_old | psql maildelay
pg_dump -t auth_permission maildelay_old | psql maildelay
pg_dump -t auth_user_groups maildelay_old | psql maildelay
pg_dump -t auth_user maildelay_old | psql maildelay
pg_dump -t auth_user_user_permissions maildelay_old | psql maildelay
pg_dump -t django_admin_log maildelay_old | psql maildelay
pg_dump -t django_content_type maildelay_old | psql maildelay
pg_dump -t django_session maildelay_old | psql maildelay
