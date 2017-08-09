from setuptools import setup

setup(
    name = 'NHANES-semantic-data-dictionary-annotation',
    version = '0.1',
    description = 'Scripts for extracting semantic data dictionaries from NHANES data',
    url = 'https://github.com/rashidsabbir/extractor',
    author = 'Ryan Sherman, Sabbir Rashid',
    author_email='rjsfox8@gmail.com',
    license='MIT',
    scripts = ['annotation_engine.py', 'NHANES_extractor_exp.py', 'utils.py'],
    install_requires=[
          'labkey',
          'PyDictionary',
          'sklearn',
          'multiprocessing',
          'inflect',
          'urllib2',
          'requests',
          'urllib',
          'bs4',
          'lxml',
          'numpy',
          'scipy'
      ],
    zip_safe = False)
