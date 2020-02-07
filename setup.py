from distutils.core import setup
import os
import sys

_minimum_version = (3, 6)

if sys.version_info < _minimum_version:
    raise RuntimeError('Required Python {}'.format(
        '.'.join([str(i) for i in _minimum_version])
    ))


setup(name='xmode',
      version='0.4',
      description='Experimental Libraries and Common Tools for Code/Data Analysis',
      author='Juti Noppornpitak',
      author_email='jnopporn@shiroyuki.com',
      url='https://github.com/shiroyuki/xmode',
      packages=['xmode',
                'xmode.db',
                'xmode.providers',
                'xmode.utils'],
      classifiers = [#'Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 3',
                     'Topic :: Software Development :: Libraries'],
      scripts = ['bin/xmode'],
      install_requires = ['kotoba',
                          'imagination',
                          'gallium'],
      python_requires = '>=3.6',
)
