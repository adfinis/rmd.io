# rmd.io
A mail reminder service written in django

## Installation

**Requirements**
* python 2.7
* docker
* docker-compose

After installing and configuring those requirements, you should be able to run the following
commands to complete the installation:
```bash
$ make install                                 # Install Python requirements
$ docker-compose up -d                         # Start the containers
$ ./manage.py migrate                          # Run Django migrations
$ ./manage.py createsuperuser                  # Create a new Django superuser
```

You can now access the application at http://localhost:8000 and the admin interface at http://localhost:8000/admin/

## License
Code released under the [GNU Affero General Public License v3.0](LICENSE).
