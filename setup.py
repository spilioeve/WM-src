from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
import subprocess
import time
import os

def parse_requirements(requirements, ignore=('setuptools')):
    """Read dependencies from requirements file (with version numbers if any)
    Note: this implementation does not support requirements files with extra
    requirements
    """
    with open(requirements) as f:
        packages = set()
        for line in f:
            line = line.strip()
            if line.startswith(('#', '-r', '--')):
                continue
            if '#egg=' in line:
                line = line.split('#egg=')[1]
            pkg = line.strip()
            if pkg not in ignore:
                packages.add(pkg)

    return tuple(packages)


def install_corenlp():
    print("Installing CoreNLP Python interface")
    os.system('git clone https://github.com/stanfordnlp/python-stanford-corenlp.git corenlp-repo')
    os.chdir('corenlp-repo')
    os.system('python setup.py install')
    os.system('easy_install .')
    os.chdir('..')
    print("Proceeding...")


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        install_corenlp()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install_corenlp()
        install.run(self)    


def main():    
    setup(name='SOFIA',
          version='0.10',
          description='SOFIA Information Extraction System',
          long_description='SOFIA is an Information Extraction system '
                           'that currently detects Causal Relationships '
                           'explicitly mentioned in the same sentence. '
                           'SOFIA is built based upon prominent Linguistic '
                           'Theories that view Causality as a discourse '
                           'relation between two Eventualities.',
          author='Evangelia Spiliopoulou',
          author_email='',
          url='',
          packages=['sofia'],
          install_requires=parse_requirements('requirements.txt', ignore=('stanford-corenlp==3.9.2')),
          include_package_data=True,
          dependency_links=['https://github.com/stanfordnlp/python-stanford-corenlp/tarball/master#egg=python-stanford-corenlp-3.9.2'],
          cmdclass={
                    'develop': PostDevelopCommand,
                    #'install': PostInstallCommand,
                   },
        )

# TODO: determine why PostDevelopCommand does not work but PostInstallCommand does; 
# on install it then skips including requirements
# so it is commented out for now.

if __name__ == '__main__':
    main()
