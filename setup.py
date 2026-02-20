import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'ntrip_client'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kikai',
    maintainer_email='igarashi.jetson@gmail.com',
    description='NTRIP client for receiving RTCM correction data via ROS2',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'ntrip_client_node = ntrip_client.ntrip_client_node:main',
        ],
    },
)
