"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

import glob
import pathlib
import subprocess

from setuptools import setup, find_packages
from setuptools.command.install import install
import os
here = os.path.abspath(os.path.dirname(__file__))
name = 'exp1572'
description = 'Console game manager for the "1572: The Lost Expedition" solitaire game'
project_urls = {
	'Bug Reports': 'https://github.com/witdba/ ' + name + '/issues',
	'Say Thanks!': 'http://saythanks.io/to/witdba',
	'Source': 'https://github.com/witdba/' + name,
}

# Translation catalogs
PO_FILES = name + '/locales/*/LC_MESSAGES/' + name + '.po'

# Compiled translations are not distributed via github (by default),
# so make them during setup
def create_mo_files():
	mo_files = []
	prefix = name

	for po_path in glob.glob(str(pathlib.Path(prefix) / PO_FILES)):
		mo = pathlib.Path(po_path.replace('.po', '.mo'))

		subprocess.run(['msgfmt', '-o', str(mo), po_path], check=True)
		mo_files.append(str(mo.relative_to(prefix)))

	return mo_files

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
	long_description = f.read()

# https://packaging.python.org/guides/single-sourcing-package-version/#single-sourcing-the-version
version = {}
with open(os.path.join(name, "version.py")) as fp:
	exec(fp.read(), version)

setup(
	name = name,  # Required
	version = version["__version__"],  # Required
	description = 'Game "1572: The Lost Expedition"',  # Optional
	long_description = long_description,  # Optional
	long_description_content_type = 'text/markdown',  # Optional (see note above)
	url = 'https://github.com/witdba/' + name,  # Optional
	author = 'Vitaliy Serdakovskiy',  # Optional
	author_email = 'witdba@gmail.com',  # Optional
	classifiers = [ # 
		'Development Status :: 4 - Beta',
		'Intended Audience :: End Users/Desktop',
		'Topic :: Games/Entertainment',
		'Topic :: Games/Entertainment :: Board Games',
		'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
	],
	keywords = 'python console game manager',  # Optional
	packages=find_packages(),  # Required
	python_requires='>=3.0.*',
	install_requires=['babel'],  # Optional
	include_package_data = True,
	package_data={  # Optional
		name: ['settings.json', ],
	},
	data_files=[(name, create_mo_files())],  # Optional
	entry_points={  # Optional
		'console_scripts': [
			'exp1572=exp1572.game:mainMenu',
		],
	},
	project_urls = project_urls
)