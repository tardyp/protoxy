import protoxy
import importlib
import sys
from .utils import * #noqa
from google.protobuf import descriptor_pool as descriptor_pool


def test_basic(tmp_path, default_pool):
    test_proto = tmp_path.joinpath("test.proto")
    test_proto.write_text("""
    syntax = "proto3";
    package test;
    message Test {
        string name = 1;
    }
    """)
    fds = protoxy.compile([test_proto])
    assert fds.file[0].name == "test.proto"


def test_with_options(tmp_path):
    test_proto = tmp_path.joinpath("optiontest.proto")
    test_proto.write_text("""
    syntax = "proto3";
    import "google/protobuf/descriptor.proto";
    package test;

    extend google.protobuf.MessageOptions {
        int32 test_option = 1001;
    }

    message Test {
        option (test.test_option) = 123;
        string name = 1;
    }
    """)
    # with python protobuf, extentions are only subscriptable by FieldDescriptor
    # so we must first compile our proto into a python module
    # to get the field Descriptor
    mod = protoxy.compile_as_modules([test_proto])
    test_option = mod["optiontest"].test_option
    assert mod["optiontest"].Test.DESCRIPTOR.GetOptions().Extensions[mod["optiontest"].test_option] == 123

    # this only works because the extension has been loaded before as a module
    fds = protoxy.compile([test_proto], include_imports=False)
    assert fds.file[0].message_type[0].options.Extensions[test_option] == 123

def test_module_import(tmp_path, default_pool):
    """ test for the Readme example """
    test_proto = tmp_path.joinpath("test.proto")
    test_proto.write_text("""
    syntax = "proto3";
    package test;
    message Test {
        string name = 1;
    }
    """)
    test_proto2 = tmp_path.joinpath("test2.proto")
    test_proto2.write_text("""
    syntax = "proto3";
    package test;
    message Test2 {
        string name = 1;
    }
    """)
    test_module = tmp_path.joinpath("protos.py")
    test_module.write_text("""
import pathlib, protoxy

_protos = (pathlib.Path(__file__).parent).glob("*.proto")
protoxy.compile_as_modules(_protos, dest=globals())
    """)
    sys.path.append(str(tmp_path))
    mod = importlib.import_module("protos")
    assert mod.test.Test.DESCRIPTOR.name == "Test"
    assert mod.test.Test.DESCRIPTOR.fields[0].name == "name"
    # not that by default, the module name is the same as the proto file name
    # not the package name
    assert mod.test2.Test2.DESCRIPTOR.name == "Test2"
    assert mod.test2.Test2.DESCRIPTOR.fields[0].name == "name"