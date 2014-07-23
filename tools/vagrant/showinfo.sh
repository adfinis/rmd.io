#!/bin/bash

PUBLICIP=$(
	ip addr show dev eth2 \
	| awk ' /inet/ { sub(/\/.*/, "", $2); print $2; exit }'
)

PRIVATEIP=$( \
	ip addr show dev eth1 \
	| awk ' /inet/ { sub(/\/.*/, "", $2); print $2; exit }'
)

PRIVATEIP=`printf '%-15s'  $PRIVATEIP`
PUBLICIP=`printf  '%-15s'  $PUBLICIP`

echo ""
echo "+------------------------------------------------------------------------+"
echo "|                                                                        |"
echo "| Welcome to the rmd.io environment. You can now access the              |"
echo "| application and several tools as follows:                              |"
echo "|                                                                        |"
echo "|   * Application:          Browse to http://localhost:8080              |"
echo "|   * Application (alt):    Browse to http://$PRIVATEIP             |"
echo "|   * Application (public): Browse to http://$PUBLICIP             |"
echo "|   * PHPMyAdmin   Browse to http://localhost:8080/phpmyadmin            |"
echo "|   * SSH access:  Commandline: vagrant ssh                              |"
echo "|                                                                        |"
echo "| User accounts to work with:                                            |"
echo "|     Application:     LDAP-User         / 123qwe                        |"
echo "|     phpPgAdmin:      root              / vagrant                       |"
echo "|     Shell:           vagrant           / vagrant                       |"
echo "+------------------------------------------------------------------------+"
echo ""

