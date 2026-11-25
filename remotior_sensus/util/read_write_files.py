# Remotior Sensus , software to process remote sensing and GIS data.
# Copyright (C) 2022-2026 Luca Congedo.
# Author: Luca Congedo
# Email: ing.congedoluca@gmail.com
#
# This file is part of Remotior Sensus.
# Remotior Sensus is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
# Remotior Sensus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty 
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Remotior Sensus. If not, see <https://www.gnu.org/licenses/>.

"""
Tools to manage text files
"""

from remotior_sensus.core import configurations as cfg
from remotior_sensus.util.files_directories import (
    create_parent_directory as file_create_parent_directory
)


# write file
def write_file(data, output_path, create_parent_directory=True, mode='w'):
    cfg.logger.log.debug('output_path: %s' % output_path)
    if create_parent_directory:
        file_create_parent_directory(output_path)
    # save combination to table
    with open(output_path, mode) as output_file:
        output_file.write(data)
    return output_path


# open text file
def open_text_file(input_path):
    with open(input_path, 'r') as f:
        text = f.read()
    cfg.logger.log.debug('input_path: %s' % str(input_path))
    return text




