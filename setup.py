from setuptools import setup, find_packages

setup(
    name='prepare_tools',
    version='0.0.1',
    url='https://github.com/openfonts-jp/prepare_tools',
    license='MIT',
    author='3846masa',
    author_email='3846masahiro+git@gmail.com',
    description='',
    long_description='',
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines()[1:],
    entry_points={
        'console_scripts': ['prepare_tools=prepare_tools:main'],
    },
    package_data={
        '': ['groups/*', 'templates/**/*'],
    },
)
