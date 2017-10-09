import setuptools



setuptools.setup(
    name='epcpm',
    use_scm_version={'version_scheme': 'post-release'},
    author="EPC Power Corp.",
    classifiers=[
        ("License :: OSI Approved :: "
         "GNU General Public License v2 or later (GPLv2+)")
    ],
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'gui_scripts': [
            'epcpm = epcpm.__main__:_entry_point',
        ],
        'console_scripts': [
            'epcparameterstoc = epcpm.parameterstoc:cli',
        ],
    },
    install_requires=[
        'click',
        'pyqt5',
        'sip',
    ],
    extras_require={
        'tests': [
            'codecov',
            'pytest',
            'pytest-cov',
            'pytest-qt',
            'tox',
        ],
    },
    setup_requires=[
        'setuptools_scm',
    ],
)
