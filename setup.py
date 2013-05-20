#!/usr/bin/env python

import os
from distutils.core import setup
from distutils.command.install_scripts import install_scripts

class post_install(install_scripts):

    def run(self):
        install_scripts.run(self)

        from shutil import move
        for i in self.get_outputs():
            n = i.replace('.py', '')
            move(i, n)
            print "moving '{0}' to '{1}'".format(i, n)


def collect_data_files():

    data_files = []

    for directory, directories, files in os.walk('src/data'):
        rel_dir = directory.replace('src/data/', '')
        for file_ in files:
            data_files.append((
                    os.path.join('share/{0}/data'.format(NAME), rel_dir),
                    [os.path.join(directory, file_)]
            ))

    data_files.append(('share/{0}/data'.format(NAME), ['src/melange.png']))
    data_files.append(('share/{0}'.format(NAME), ['src/manifest.xml']))

    return data_files


NAME = 'cream-melange'

data_files = collect_data_files()
data_files.extend(
    [
    ('share/{0}/configuration'.format(NAME),
        ['src/configuration/scheme.xml']),
    ('share/icons',
        ['src/melange.png']),
    ('share/applications',
        ['src/melange.desktop'])
    ])


setup(
    name = 'melange',
    version = '0.5',
    author = 'The Cream Project (http://cream-project.org)',
    url = 'http://github.com/cream/melange',
    package_dir = {'melange': 'src/melange'},
    package_data={'melange': ['add_dialog.glade', 'images/*']},
    packages = ['melange'],
    data_files = data_files,
    cmdclass={'install_scripts': post_install},
    scripts = ['src/melange.py']
)
