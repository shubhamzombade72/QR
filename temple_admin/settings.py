from pathlib import Path
import os
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'crispy_forms',
	'crispy_bootstrap5',
	'payments',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'temple_admin.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [os.path.join(BASE_DIR, 'templates')],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = 'temple_admin.wsgi.application'

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': BASE_DIR / 'db.sqlite3',
	}
}


AUTH_PASSWORD_VALIDATORS = [
	{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
	{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
	{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
	{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Message framework configuration
MESSAGE_TAGS = {
	messages.DEBUG: 'alert-info',
	messages.INFO: 'alert-info',
	messages.SUCCESS: 'alert-success',
	messages.WARNING: 'alert-warning',
	messages.ERROR: 'alert-error',
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'your-email@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'your-app-password')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Razorpay Settings
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_pxbxGUT7Fo6eRc')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'y2QDnNlmsT9bglSWhBbPr2Qm')

# Gmail API Settings
GMAIL_API_CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
GMAIL_USER_EMAIL = os.getenv('GMAIL_USER_EMAIL', 'szombade4589v@gmail.com')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
GMAIL_TOKEN_PATH = os.path.join(BASE_DIR, 'token.pickle')
