from setuptools import setup, find_packages

setup(
    name='twinyields',
    version='0.1.0',
    #packages=['twinyields', 'twinyields.eo', 'twinyields.eo.common', 'twinyields.eo.aws_cog', 'twinyields.eo.biophys',
    #          'twinyields.sensors', 'twinyields.database'],
    url='https://github.com/TwinYields/twinyields-python',
    license='MIT',
    author='Matti Pastell, Victor Bloch, Katariina Pussi',
    author_email='matti.pastell@luke.fi',
    description='Package for running a Digital Twin of crop farming system',
    packages = find_packages(),
    include_package_data = True,
    entry_points={
          'console_scripts': 
            ['twinyields = twinyields:twinyields_cli']
          }
)
