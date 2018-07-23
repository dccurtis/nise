#
# Copyright 2018 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import os
import shutil
from tempfile import (mkdtemp, NamedTemporaryFile)
from unittest import TestCase

from nise.copy import copy_to_local_dir


class CopyTestCase(TestCase):
    """
    TestCase class for copy
    """

    def test_copy_success(self):
        """Test copy_to_local_dir method."""
        source_file = NamedTemporaryFile(delete=False)
        source_file.seek(0)
        source_file.write(b'cur report')
        source_file.flush()

        bucket_name = mkdtemp()
        bucket_file_path = '/bucket_location'

        success = copy_to_local_dir(bucket_name, bucket_file_path, source_file.name)
        self.assertTrue(success)

        expected_full_bucket_path = '{}{}'.format(bucket_name, bucket_file_path)
        self.assertTrue(os.path.isdir(expected_full_bucket_path))

        expected_file_location = '{}/{}'.format(expected_full_bucket_path,
                                                os.path.basename(source_file.name))
        self.assertTrue(os.path.isfile(expected_file_location))

        shutil.rmtree(bucket_name)
        os.remove(source_file.name)

    def test_copy_failure(self):
        """Test copy_to_local_dir method when local directory (bucket does not exist)."""
        source_file = NamedTemporaryFile(delete=False)
        source_file.seek(0)
        source_file.write(b'cur report')
        source_file.flush()

        bucket_name = mkdtemp()
        bad_bucket_name = bucket_name + 'bad'
        bucket_file_path = '/bucket_location'

        success = copy_to_local_dir(bad_bucket_name, bucket_file_path, source_file.name)
        self.assertFalse(success)

        shutil.rmtree(bucket_name)
        os.remove(source_file.name)