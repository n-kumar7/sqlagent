from setuptools import setup, find_packages

setup(
    name='my_app',                      # replace with your app's name
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        "openai==0.27.0",
        "psycopg2-binary==2.9.6"
    ],
    entry_points={
        'console_scripts': [
            'my_app=app.main:main',         # updated to reference app/main.py's main()
        ],
    },
)
