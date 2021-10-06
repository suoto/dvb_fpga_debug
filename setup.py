# This file is part of HDL Checker.
#
# Copyright (c) 2015 - 2019 suoto (Andre Souto)
#
# HDL Checker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HDL Checker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HDL Checker.  If not, see <http://www.gnu.org/licenses/>.
"HDL Checker installation script"

import setuptools  # type: ignore

setuptools.setup(
    name="dvb",
    version="0.1",
    description="DVB Helper",
    author="Andre Souto",
    author_email="andre820@gmail.com",
    platforms="any",
    packages=setuptools.find_packages(),
    install_requires=[
        "argcomplete",
        "argparse",
        'backports.functools_lru_cache; python_version<"3.2"',
        "bottle>=0.12.9",
        'enum34>=1.1.6; python_version<"3.3"',
        "requests>=2.20.0",
        "tabulate>=0.8.5",
        "typing>=3.7.4",
        "waitress>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "dvb_status=__main__:printStatus",
        ]
    },
)
