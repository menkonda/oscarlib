from setuptools import setup, find_packages

setup(
	name='oscarlib',
	version='0.0.1',
	description='A python library for Oscar Project automation',
	long_description='A python library for Oscar Project automation. This library shall be used for maintenance and testing on RMS, IGR, TXT',
	url='https://github.com/menkonda/rms_api',
	author='Manuel ENKONDA',
	
	keywords='Oracle RMS Auchan Retail Automation',
	packages=find_packages(),
	
	install_requires=['cx_Oracle >= 6.0rc2','python-dateutil','paramiko'],
	python_requires='>=3.3',
	package_data={
		'rms':'rms_templates/*'
	},
	include_package_data=True
	
)
	
	
	
