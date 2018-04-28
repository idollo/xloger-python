from setuptools import setup

setup(
    name='xloger',
    version="1.5.1",
    url='https://github.com/idollo/xloger-python.git',
    license='MIT',
    author='idollo',
    author_email='stone58@qq.com',
    description='python client lib for xloger.',
    long_description=__doc__,
    packages=['xloger'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        "socketpool>=0.5.3"
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ]
)
