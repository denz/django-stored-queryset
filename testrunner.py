import sys
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test.db',
                'USER': '',
                'PASSWORD': '',
                'HOST': '',
                'PORT': '',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'test.stored',

        ],
    )

from django.test.simple import DjangoTestSuiteRunner
DEFAULT_TESTED_APPS = ('stored', )


def runtests():
    failures = DjangoTestSuiteRunner().run_tests(DEFAULT_TESTED_APPS)
    sys.exit(failures)

if __name__ == '__main__':
    runtests()
