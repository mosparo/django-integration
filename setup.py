from setuptools import find_packages, setup

long_description = (
    open("README.md", "rb").read().decode("utf-8")
)

setup(
    name="mosparo_django",
    version="1.0.0",
    description="A Django app to integrate mosparo into your forms.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="mosparo Core Developers",
    author_email="info@mosparo.io",
    keywords=['mosparo', 'spam-protection', 'accessibility', 'captcha', 'django', 'app'],
    license="MIT",
    url="https://github.com/mosparo/django-integration",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
    ],
    packages=find_packages(),
    install_requires=['mosparo', 'Django>=3.2'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
    include_package_data=True,
    python_requires='>=3.6',
)