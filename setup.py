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

    for directory, directories, files in os.walk('data/'):
        rel_dir = directory.replace('data/', '')
        for file_ in files:
            data_files.append((
                    os.path.join('share/{0}'.format(NAME), rel_dir),
                    [os.path.join(directory, file_)]
            ))

    return data_files


NAME = 'cream-melange'

data_files = collect_data_files()

setup(
    name = 'melange',
    version = '0.5.1',
    author = 'The Cream Project (http://cream-project.org)',
    url = 'http://github.com/cream/melange',
    package_dir = {'cream.melange': 'src/melange'},
    packages = ['cream.melange'],
    data_files = data_files,
    cmdclass={'install_scripts': post_install},
    scripts = ['src/melange.py']
)
