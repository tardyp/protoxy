import sys
import importlib.machinery
from importlib import import_module

MODULES_DATA = {}

TMPL = """
from typing import TYPE_CHECKING
from protoxy.importer import MODULES_DATA
from google.protobuf import descriptor_pool
from google.protobuf.internal import builder as _builder

{deps}
if TYPE_CHECKING:
{stubs}
else:
    pool = descriptor_pool.Default()
    for data in MODULES_DATA["{path}"]['fd']:
        DESCRIPTOR = pool.AddSerializedFile(data)
        _builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
        _builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "{module_name}", globals())
"""
class Loader(importlib.machinery.SourceFileLoader):
    def get_data(self, path):
        ret = TMPL.format(
            stubs="\n".join(MODULES_DATA[path]['stubs']),
            path=path,
            deps="\n".join(f"import {d}" for d in MODULES_DATA[path]['deps']),
            module_name=path.split(".")[-1]
        )
        MODULES_DATA[path]['generated'] = ret
        return ret.encode("utf-8")

class Finder(importlib.machinery.PathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in MODULES_DATA:
            return importlib.machinery.ModuleSpec(fullname, Loader(fullname, fullname), origin=fullname)

sys.meta_path.insert(0, Finder())
GOOGLE_DEPS = {
    'google.protobuf.any': 'google.protobuf.any_pb2',
    'google.protobuf.api': 'google.protobuf.api_pb2',
    'google.protobuf.compiler': 'google.protobuf.compiler.plugin_pb2',
    'google.protobuf.descriptor': 'google.protobuf.descriptor_pb2',
    'google.protobuf.duration': 'google.protobuf.duration_pb2',
    'google.protobuf.empty': 'google.protobuf.empty_pb2',
    'google.protobuf.field_mask': 'google.protobuf.field_mask_pb2',
    'google.protobuf.source_context': 'google.protobuf.source_context_pb2',

}
def gen_modules(modules, dest, prefix):
    for m in modules:
        full_name = prefix + "." + m.package
        data = MODULES_DATA.setdefault(full_name,{'fd':[], 'deps': set(), 'stubs': []})
        data['fd'].append(m.fd)
        data['stubs'].append(m.typing_stub)
        for d in m.dep_names:
            if d in GOOGLE_DEPS:
                data['deps'].add(GOOGLE_DEPS[d])
            else:
                d = prefix + "." + d
                data['deps'].add(d)

    for m in modules:
        try:
            dest[m.package] = import_module(full_name)
        except ImportError:
            print(MODULES_DATA[full_name].get('generated'))
            raise