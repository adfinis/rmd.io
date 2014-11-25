# Django settings for maildelay project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'maildelay',
        'USER': 'maildelay',
        'PASSWORD': 'vagrant',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Zurich'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_URL = 'https://maildelay.vm'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/vagrant/app/static'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don'ys use forward slashes, even on Windows.
    # os.path.join(os.getcwd(), "static"),
    # '/vagrant/app/static'
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'qkk)_bi42*bikzfakx3)vqlr$7o3vn92z*or66c@8z2)$o767d'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'maildelay.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'maildelay.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/vagrant/app/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django_browserid',
    'django_extensions',
    'mails',
    'south',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_browserid.auth.BrowserIDBackend'
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django_browserid.context_processors.browserid',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = False

LOGIN_REDIRECT_URL = '/mails/'

LOGIN_REDIRECT_URL_FAILURE = '/login/'

LOGOUT_REDIRECT_URL = '/login/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format'  : ("[%(asctime)s] %(levelname)s "
                         "[%(name)s:%(lineno)s] %(message)s"),
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format'  : '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level'     : 'DEBUG',
            'class'     : 'logging.FileHandler',
            'filename'  : '/var/log/django/error.log',
            'formatter' : 'verbose',
        }
    },
    'loggers': {
        'django_browserid': {
            'handlers': ['file'],
            'level'   : 'DEBUG',
            'filename': '/var/log/browserid-debug.log',
        },
        'mails': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    }
}

CSP_SCRIPT_SRC = ("'self'", 'https://login.persona.org')
CSP_FRAME_SRC = ("'self'", 'https://login.persona.org')


# Mailserver login settings

EMAIL_HOST_USER = 'maildelay@maildelay.ml'
EMAIL_HOST_PASSWORD = '3p7KDn4FugQQ'
EMAIL_HOST = 'maildelay.ml'
EMAIL_FOLDER = 'INBOX'

MAILBOXES = [
    ('1d', 'Mail Delay for 1 day'),
    ('2d', 'Mail Delay for 2 days'),
    ('3d', 'Mail Delay for 3 days'),
    ('4d', 'Mail Delay for 4 days'),
    ('5d', 'Mail Delay for 5 days'),
    ('6d', 'Mail Delay for 6 days'),
    ('7d', 'Mail Delay for 7 days'),
    ('8d', 'Mail Delay for 8 days'),
    ('9d', 'Mail Delay for 9 days'),
    ('10d', 'Mail Delay for 10 days'),
    ('11d', 'Mail Delay for 11 days'),
    ('1w', 'Mail Delay for 1 week'),
    ('2w', 'Mail Delay for 2 weeks'),
    ('3w', 'Mail Delay for 3 weeks'),
    ('4w', 'Mail Delay for 4 weeks'),
    ('5w', 'Mail Delay for 5 weeks'),
    ('6w', 'Mail Delay for 6 weeks'),
    ('7w', 'Mail Delay for 7 weeks'),
    ('8w', 'Mail Delay for 8 weeks'),
    ('9w', 'Mail Delay for 9 weeks'),
    ('10w', 'Mail Delay for 10 weeks'),
    ('11w', 'Mail Delay for 11 weeks'),
    ('1m', 'Mail Delay for 1 month'),
    ('2m', 'Mail Delay for 2 months'),
    ('3m', 'Mail Delay for 3 months'),
    ('4m', 'Mail Delay for 4 months'),
    ('5m', 'Mail Delay for 5 months'),
    ('6m', 'Mail Delay for 6 months'),
    ('7m', 'Mail Delay for 7 months'),
    ('8m', 'Mail Delay for 8 months'),
    ('9m', 'Mail Delay for 9 months'),
    ('10m', 'Mail Delay for 10 months'),
    ('11m', 'Mail Delay for 11 months'),
]
