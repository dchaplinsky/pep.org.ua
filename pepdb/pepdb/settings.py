# coding: utf-8
"""
Django settings for pepdb project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

def get_env_str(k, default):
    return os.environ.get(k, default)

def get_env_str_list(k, default=""):
    if os.environ.get(k) is not None:
        return os.environ.get(k).strip().split(" ")
    return default

def get_env_int(k, default):
    return int(get_env_str(k, default))

def get_env_bool(k, default):
    return str(get_env_str(k, default)).lower() in ["1", "y", "yes", "true"]


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# For stupid sitemaps
SITE_URL = "https://pep.org.ua"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_str('SECRET_KEY', '*37e&4-qi$f+paw#=me8opo$uk7y%d$c@crd++q89$4y!g$p!e')
FERNET_SECRET_KEY = get_env_str('FERNET_SECRET_KEY', '')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = get_env_str_list('ALLOWED_HOSTS', [])


# Application definition
SITE_ID = 1

INSTALLED_APPS = (
    'grappelli',
    'grappelli_modeltranslation',
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.postgres',
    'django_otp',
    'django_otp.plugins.otp_totp',

    'redactor',
    'pipeline',
    'django_jinja',
    'django_jinja.contrib._humanize',
    'django_jinja.contrib._easy_thumbnails',

    'easy_thumbnails',
    'taggit',
    'modelcluster',

    'wagtail.wagtailcore',
    'wagtail.wagtailadmin',
    'wagtail.wagtaildocs',
    'wagtail.wagtailsnippets',
    'wagtail.wagtailusers',
    'wagtail.wagtailimages',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsites',
    'wagtail.wagtailsearch',
    'wagtail.wagtailredirects',
    'wagtail.wagtailforms',
    'django_pickling',
    'nested_admin',
    'cacheops',
    'django_neomodel',

    'cms_pages',
    'qartez',
    'captcha',
    'core',
    'tasks',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
)

from django_jinja.builtins import DEFAULT_EXTENSIONS

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "context_processors": (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.feedback_processor",
                "core.context_processors.config_processor",
                "core.context_processors.default_country",
                "cms_pages.context_processors.menu_processor"
            ),
            "extensions": DEFAULT_EXTENSIONS + [
                "jinja2.ext.do",
                "jinja2.ext.loopcontrols",
                "jinja2.ext.with_",
                "jinja2.ext.i18n",
                "jinja2.ext.autoescape",
                "django_jinja.builtins.extensions.CsrfExtension",
                "django_jinja.builtins.extensions.CacheExtension",
                "django_jinja.builtins.extensions.TimezoneExtension",
                "django_jinja.builtins.extensions.UrlsExtension",
                "django_jinja.builtins.extensions.StaticFilesExtension",
                "django_jinja.builtins.extensions.DjangoFiltersExtension",
                "pipeline.jinja2.PipelineExtension",
                "wagtail.wagtailcore.jinja2tags.core",
                "wagtail.wagtailimages.jinja2tags.images",
            ]
        }
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "OPTIONS": {
            "context_processors": (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.feedback_processor",
                "core.context_processors.config_processor",
                "core.context_processors.default_country",
                "cms_pages.context_processors.menu_processor"
            )
        },
        "APP_DIRS": True
    },
]

GRAPPELLI_ADMIN_TITLE = u"(Секретна) база даних PEP"

ROOT_URLCONF = 'pepdb.urls'

WSGI_APPLICATION = 'pepdb.wsgi.application'


DATABASES = {
    "default": {
        # Strictly PostgreSQL
        "ENGINE": 'django.db.backends.postgresql_psycopg2',
        "NAME": get_env_str('DB_NAME', "pep"),
        "USER": get_env_str('DB_USER', "pep"),
        "PASSWORD": get_env_str('DB_PASS', ""),
        "HOST": get_env_str('DB_HOST', "127.0.0.1"),
        "PORT": "5432",
    }
}

# Internationalization
LANGUAGE_CODE = 'uk'

gettext = lambda s: s
LANGUAGES = (
    ('uk', gettext('Ukrainian')),
    ('en', gettext('English')),
)
LANGUAGE_CODES = list(dict(LANGUAGES).keys())

TIME_ZONE = 'Europe/Kiev'

USE_I18N = True
USE_L10N = True
USE_TZ = True


LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
)

DATE_FORMAT = "d.m.Y"
MONTH_YEAR_DATE_FORMAT = "m.Y"
YEAR_DATE_FORMAT = "Y"

FORMAT_MODULE_PATH = [
    'core.formats',
]

DEFAULT_JINJA2_TEMPLATE_EXTENSION = '.jinja'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
MEDIA_ROOT = get_env_str('MEDIA_ROOT', os.path.join(BASE_DIR, "media"))
STATIC_ROOT = get_env_str('STATIC_ROOT', os.path.join(BASE_DIR, "static"))
MEDIA_URL = '/media/'

REDACTOR_OPTIONS = {'lang': 'ua', 'air': True}
REDACTOR_UPLOAD = 'uploads/'


JINJA2_EXTENSIONS = ["pipeline.jinja2.ext.PipelineExtension"]

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    'pipeline.finders.PipelineFinder',
)

PIPELINE = {
    'COMPILERS': ('pipeline.compilers.less.LessCompiler',),
    'JS_COMPRESSOR': 'pipeline.compressors.uglifyjs.UglifyJSCompressor',
    'STYLESHEETS': {
        'css_all': {
            'source_filenames': (
                'css/flag-css.css',
                'css/vis.css',
                'css/graph.css',
                "css/tippy.css",
                "css/tippy-light.css",
                'css/app.css',
                'css/simplebar.css',
                'css/perfect-scrollbar.min.css',
                'css/slick.css',
                'css/slick-theme.css',
            ),
            'output_filename': 'css/merged.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },

        'css_print': {
            'source_filenames': (
                'css/print.css',
            ),
            'output_filename': 'css/merged_print.css',
            'extra_context': {
                'media': 'print',
            },
        },
    },

    'JAVASCRIPT': {
        'js_all': {
            'source_filenames': (
                "js/jQuery-3.4.1.min.js",
                "bower_components/bootstrap/dist/js/bootstrap.js",
                "bower_components/bootstrap/js/tab.js",
                "bower_components/bootstrap3-typeahead/bootstrap3-typeahead.js",
                "bower_components/jquery.nicescroll/jquery.nicescroll.min.js",
                "js/bootstrap-combobox.js",
                "js/pep.js",
                "js/chart.js",
                "js/main.js",
                "js/simplebar.js",
                "js/slick.js",
                "js/particles.js"
            ),
            'output_filename': 'js/merged.js',
        },
        "graph_viz": {
            "source_filenames": (
                "bower_components/cytoscape/dist/cytoscape.min.js",
                "bower_components/popper.js/dist/umd/popper.js",
                "bower_components/cytoscape-popper/cytoscape-popper.js",
                "bower_components/cytoscape-euler/cytoscape-euler.js",
                "bower_components/cytoscape-dagre/cytoscape-dagre.js",
                "js/tippy.js",
                "js/cytograph_init.js",
            ),
            "output_filename": "js/cytograph.js",
        }
    }
}


LOGIN_URL = "/admin/login/"
WAGTAIL_SITE_NAME = 'PEP'


# Setup Elasticsearch default connection
ELASTICSEARCH_CONNECTIONS = {
    'default': {
        "hosts": get_env_str('ELASTICSEARCH_DSN', "localhost:9200"),
        'timeout': 120
    }
}

THUMBNAIL_ALIASES = {
    '': {
        'small_avatar': {'size': (240, 240), 'crop': True, 'upscale': True},
        'avatar': {'size': (600, 600), 'crop': True, 'upscale': True},
        'article': {'size': (800, 800), 'crop': False},
    },
}

CATALOG_PER_PAGE = 12

RECAPTCHA_PUBLIC_KEY = get_env_str("RECAPTCHA_PUBLIC_KEY", "")
RECAPTCHA_PRIVATE_KEY = get_env_str("RECAPTCHA_PRIVATE_KEY", "")
NOCAPTCHA = True
RECAPTCHA_USE_SSL = True

DECLARATIONS_SEARCH_ENDPOINT = "https://declarations.com.ua/fuzzy_search"
DECLARATION_DETAILS_ENDPOINT = "https://declarations.com.ua/declaration/{}"
DECLARATION_DETAILS_EN_ENDPOINT = "https://declarations.com.ua/en/declaration/{}"
CACHEOPS_REDIS = get_env_str("CACHEOPS_REDIS", "redis://localhost:6379/1")
SCORING_FILE = get_env_str("SCORING_FILE", "")

CACHEOPS = {
    'core.*': {
        'ops': 'all', 'timeout': 12 * 60 * 60
    }
}

CACHEOPS_DEGRADE_ON_FAILURE = True
DEFAULT_COUNTRY_ISO3 = "UKR"

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

OTP_TOTP_ISSUER = 'PEP.org.ua'
SITEHEART_ID = get_env_str("SITEHEART_ID", None)
GA_ID = get_env_str("GA_ID", None)
SUPERADMINS = []

NEO4J_ADMIN_PATH = get_env_str("NEO4J_ADMIN_PATH", "")
NEO4J_DATABASE_NAME = get_env_str("NEO4J_DATABASE_NAME", "")
NEOMODEL_NEO4J_BOLT_URL = get_env_str("NEOMODEL_NEO4J_BOLT_URL", 'bolt://neo4j:test@localhost:7687')
ES_NUMBER_OF_SHARDS = get_env_int("ES_NUMBER_OF_SHARDS", 3)
ES_NUMBER_OF_REPLICAS = get_env_int("ES_NUMBER_OF_REPLICAS", 0)
ES_MAX_RESULT_WINDOW = 100000
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

WATERMARKS_PATH = "tasks/static/watermarks/*.pdf"
OPENEXCHANGERATES_KEY = ""

try:
    from local_settings import *
except ImportError:
    pass

# Init Elasticsearch connections
from elasticsearch_dsl import connections
connections.connections.configure(**ELASTICSEARCH_CONNECTIONS)


# Init fernet instance
from cryptography.fernet import Fernet
SYMMETRIC_ENCRYPTOR = Fernet(FERNET_SECRET_KEY)
