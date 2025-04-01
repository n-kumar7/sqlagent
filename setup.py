from setuptools import setup, find_packages

setup(
    name='my_app',                      # replace with your app's name
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        "openai>=0.27.5",  # updated to ensure new SDK is installed
        "psycopg2-binary==2.9.6"
    ],
    entry_points={
        'console_scripts': [
            'my_app=app.main:main',
        ],
    },
)
