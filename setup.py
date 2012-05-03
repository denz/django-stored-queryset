#!/usr/bin/env python

from importlib import import_module

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test


def package_env(file_name, strict=False):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(file_path) or strict:
        return open(file_path).read()
    else:
        return u''

PROJECT = u'django-stored-queryset'

VERSION = package_env('VERSION')
URL = package_env('URL')

AUTHOR_AND_EMAIL = [v.strip('>').strip() for v \
                    in package_env('AUTHOR').split('<mailto:')]

if len(AUTHOR_AND_EMAIL) == 2:
    AUTHOR, AUTHOR_EMAIL = AUTHOR_AND_EMAIL
else:
    AUTHOR = AUTHOR_AND_EMAIL
    AUTHOR_EMAIL = u''

DESC = "pickleable Django QuerySet"


class TestRunner(test):
    def run(self, *args, **kwargs):
        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(self.\
                                                distribution.install_requires)
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)
        from testrunner import runtests

        runtests()

if __name__ == '__main__':
    setup(
        cmdclass={"test": TestRunner},
        name=PROJECT,
        version=VERSION,
        description=DESC,
        long_description=package_env('README.rst'),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
        license=package_env('LICENSE'),
        packages=find_packages(),
        package_dir={'stored': 'stored'},
        include_package_data=True,
        zip_safe=True,
        test_suite='test',
        install_requires=['django', ],
        classifiers=[
            'License :: OSI Approved',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Framework :: Django',
        ],
    )
