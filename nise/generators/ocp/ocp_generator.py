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
"""Defines the abstract generator."""
import datetime
from copy import deepcopy
from random import choice, choices, randint, uniform
from string import ascii_lowercase

from nise.generators.generator import AbstractGenerator


OCP_COLUMNS = ('report_period_start', 'report_period_end', 'pod', 'namespace',
               'node', 'interval_start', 'interval_end',
               'pod_usage_cpu_core_seconds', 'pod_request_cpu_core_seconds',
               'pod_limit_cpu_core_seconds', 'pod_usage_memory_byte_seconds',
               'pod_request_memory_byte_seconds', 'pod_limit_memory_byte_seconds',
               'node_capacity_cpu_cores', 'node_capacity_cpu_core_seconds',
               'node_capacity_memory_bytes', 'node_capacity_memory_byte_seconds')


# pylint: disable=too-few-public-methods
class OCPGenerator(AbstractGenerator):
    """Defines a abstract class for generators."""

    def __init__(self, start_date, end_date):
        """Initialize the generator."""
        super().__init__(start_date, end_date)
        self.nodes = self._gen_nodes()
        self.namespaces = self._gen_namespaces(self.nodes)
        self.pods = self._gen_pods(self.namespaces)

    @staticmethod
    def timestamp(in_date):
        """Provide timestamp for a date."""
        if not in_date or not isinstance(in_date, datetime.datetime):
            raise ValueError('in_date must be a date object.')
        return in_date.strftime('%Y-%m-%d %H:%M:%S +0000 UTC')

    def _gen_nodes(self):
        """Create nodes for report."""
        nodes = []
        num_nodes = randint(2, 6)
        for node_num in range(0, num_nodes):  # pylint: disable=W0612
            memory_gig = randint(2, 8)
            memory_bytes = memory_gig * 1024 * 1024
            node = {'name': 'node_' + self.fake.word(),  # pylint: disable=no-member
                    'cpu_cores': randint(2, 16),
                    'memory_bytes': memory_bytes}
            nodes.append(node)
        return nodes

    def _gen_namespaces(self, nodes):
        """Create namespaces on specific nodes and keep relationship."""
        namespaces = {}
        for node in nodes:
            num_namespaces = randint(2, 12)
            for num_namespace in range(0, num_namespaces):  # pylint: disable=W0612
                namespace_suffix = choice(('ci', 'qa', 'prod', 'proj', 'dev', 'staging'))
                namespace = self.fake.word() + '_' + namespace_suffix  # pylint: disable=no-member
                namespaces[namespace] = node
        return namespaces

    def _gen_pods(self, namespaces):  # pylint: disable=too-many-locals
        """Create pods on specific namespaces and keep relationship."""
        pods = {}
        hour = 60 * 60
        for namespace, node in namespaces.items():
            num_pods = randint(2, 20)
            for num_namespace in range(0, num_pods):  # pylint: disable=W0612
                pod_suffix = ''.join(choices(ascii_lowercase, k=5))
                pod_type = choice(('build', 'deploy', pod_suffix))
                pod = self.fake.word() + '_' + pod_type  # pylint: disable=no-member
                cpu_cores = node.get('cpu_cores')
                memory_bytes = node.get('memory_bytes')
                cpu_request = round(uniform(0.02, 1.0), 5)
                mem_request = round(uniform(250000000.0, 800000000.0), 2)
                pods[pod] = {'namespace': namespace,
                             'node': node.get('name'),
                             'pod': pod,
                             'node_capacity_cpu_cores': cpu_cores,
                             'node_capacity_cpu_core_seconds': cpu_cores * hour,
                             'node_capacity_memory_bytes': memory_bytes,
                             'node_capacity_memory_byte_seconds': memory_bytes * hour,
                             'cpu_request': cpu_request,
                             'cpu_limit': round(uniform(cpu_request, 1.0), 5),
                             'mem_request': mem_request,
                             'mem_limit': round(uniform(mem_request, 800000000.0), 2), }
        return pods

    def _init_data_row(self, start, end):  # noqa: C901
        """Create a row of data with placeholder for all headers."""
        if not start or not end:
            raise ValueError('start and end must be date objects.')
        if not isinstance(start, datetime.datetime):
            raise ValueError('start must be a date object.')
        if not isinstance(end, datetime.datetime):
            raise ValueError('end must be a date object.')

        bill_begin = start.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
        bill_end = AbstractGenerator.next_month(bill_begin)
        row = {}
        for column in OCP_COLUMNS:
            row[column] = ''
            if column == 'report_period_start':
                row[column] = OCPGenerator.timestamp(bill_begin)
            elif column == 'report_period_end':
                row[column] = OCPGenerator.timestamp(bill_end)
        return row

    def _add_common_usage_info(self, row, start, end):
        """Add common usage information."""
        row['interval_start'] = OCPGenerator.timestamp(start)
        row['interval_end'] = OCPGenerator.timestamp(end)
        return row

    def _update_data(self, row, start, end, **kwargs):  # pylint: disable=too-many-locals
        """Update data with generator specific data."""
        row = self._add_common_usage_info(row, start, end)
        pod_seconds = randint(2, 60 * 60)
        pod = kwargs.get('pod')
        cpu_request = pod.pop('cpu_request')
        mem_request = pod.pop('mem_request')
        cpu_limit = pod.pop('cpu_limit')
        mem_limit = pod.pop('mem_limit')
        cpu = round(uniform(0.02, cpu_request), 5)
        mem = round(uniform(250000000.0, mem_request), 2)
        pod['pod_usage_cpu_core_seconds'] = pod_seconds * cpu
        pod['pod_request_cpu_core_seconds'] = pod_seconds * cpu_request
        pod['pod_limit_cpu_core_seconds'] = pod_seconds * cpu_limit
        pod['pod_usage_memory_byte_seconds'] = pod_seconds * mem
        pod['pod_request_memory_byte_seconds'] = pod_seconds * mem_request
        pod['pod_limit_memory_byte_seconds'] = pod_seconds * mem_limit
        row.update(pod)
        return row

    def _generate_hourly_data(self):
        """Create houldy data."""
        data = []
        for hour in self.hours:
            start = hour.get('start')
            end = hour.get('end')
            pod_count = len(self.pods)
            num_pods = randint(2, pod_count)
            pod_index_list = range(pod_count)
            pod_choices = list(set(choices(pod_index_list, k=num_pods)))
            pod_keys = list(self.pods.keys())
            for pod_choice in pod_choices:
                pod_name = pod_keys[pod_choice]
                pod = deepcopy(self.pods[pod_name])
                row = self._init_data_row(start, end)
                row = self._update_data(row, start, end, pod=pod)
                data.append(row)
        return data

    def generate_data(self):
        """Responsibile for generating data."""
        data = self._generate_hourly_data()
        return data