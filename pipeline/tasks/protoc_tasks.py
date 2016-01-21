"""Tasks related to protoc"""

import os
import subprocess
from taskflow import task
from pipeline.tasks import task_base
from pipeline.tasks.requirements import grpc_requirements


def _find_protos(proto_paths):
    """Searches along `proto_path` for .proto files and returns a list of
    paths"""
    protos = []
    for path in proto_paths:
        for root, _, files in os.walk(path):
            protos += [os.path.join(root, proto) for proto in files
                if os.path.splitext(proto)[1] == '.proto']
    return protos


class ProtoDescriptorGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, service_proto_path, import_proto_path, output_dir):
        print 'Compiling descriptors {0}'.format(_find_protos(service_proto_path))
        out_file = 'descriptor.desc'
        subprocess.call(['mkdir', '-p', output_dir])
        subprocess.call(['protoc', '--include_imports'] +
                        ['--proto_path=' + path for path in
                             (service_proto_path + import_proto_path)] +
                        ['--include_source_info',
                         '-o', os.path.join(output_dir, out_file)] +
                        _find_protos(service_proto_path))
        return os.path.join(output_dir, out_file)

    def requires():
        return [grpc_requirement.GrpcRequirement]


class GrpcCodeGenTask(task_base.TaskBase):
    """Generates the gRPC client library"""
    def execute(self, plugin, service_proto_path, import_proto_path, output_dir):
        for proto in _find_protos(service_proto_path):
            subprocess.call(
                ['protoc'] +
                ['--proto_path=' + path
                     for path in (import_proto_path + service_proto_path)] +
                ['--python_out=' + output_dir,
                 '--plugin=protoc-gen-grpc=' +
                 subprocess.check_output(['which', plugin])[:-1],
                 '--grpc_out=' + output_dir, proto])
            print 'Running protoc on {0}'.format(proto)

    def requires():
        return [grpc_requirement.GrpcRequirements]