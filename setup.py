from distutils.core import setup
import setuptools

def main():
    install_list = ['nltk==3.4', 'openpyxl==2.5.12', 'bs4==0.0.1', 
                    'pyenchant==2.0.0', 'wikipedia==1.4.0', 
                    'pandas==0.23.4', 'Flask==1.0.2', 'APScheduler==3.5.3', 
                    'redis==3.0.1']
    
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
          install_requires=install_list,
          include_package_data=True,
        )


if __name__ == '__main__':
    main()