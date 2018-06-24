import os
from setuptools import setup, find_packages


def read(fname):
    """
    Utility function to read the README file.
    Used for the long_description.  It's nice, because now 1) we have a top level README file and 2) it's easier to
    type in the README file than to put a raw string in below ...
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
setup(
    name='catankarma',
    version='0.1',
    author='Andrew Brooks',
    author_email='andrewbrooks@gmail.com',
    description='Quantifying the luck factor in Settlers of Catan by modeling resource collection distributions',
    license='MIT License',
    keywords='settlers catan probability flask',
    url='https://github.com/brooksandrew/catan-karma',
    download_url='https://github.com/brooksandrew/catan-karma/archive/master.zip',
    packages=find_packages(),
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: MIT License'
    ],
    # package_data={}
    # include_package_data=True,
    entry_points={
        'console_scripts': [
            'catan-karma=catankarma.app:main',
        ]
    },
    python_requires='>=2.7',
    install_requires=[
        'scipy',  # may not need
        'pandas',
        'numpy',
        'parse',
        'flask',
        'requests',
        'hexgrid',
        'catan-spectator==0.1.4'
    ],
    extras_require={
        'test': ['pytest', 'pytest-cov', 'pytest-console-scripts']
    },
    dependency_links=[
        'https://github.com/brooksandrew/catan-spectator/tarball/master#egg=catan-spectator-0.1.4'
    ]
)


