from setuptools import setup, find_packages

setup(
    name='k5dstatus',
    version='0.0.3',
    author='James Bliss',
    author_email='astronouth7303',
    url='https://github.com/astronouth7303/k5dstatus',
    license='BSD',
    description='The ultimate DIY statusline generator for i3',
    long_description=open('README.rst').read(),

    install_requires=['PyYAML', 'i3ipc', 'ijson', 'netifaces', 'setuptools'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],

    package_data={'k5dstatus': ['generators/*']},

    scripts=['k5-dstatus'],

    packages=find_packages(),
)
