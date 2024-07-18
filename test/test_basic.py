import protoxy

def test_basic(tmp_path):
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
    test_proto = tmp_path.joinpath("test.proto")
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
    test_option = mod.test_pb2.test_option
    assert mod.test_pb2.Test.DESCRIPTOR.GetOptions().Extensions[mod.test_pb2.test_option] == 123

    # this only works because the extension has been loaded before as a module
    fds = protoxy.compile([test_proto], include_imports=False)
    assert fds.file[0].message_type[0].options.Extensions[test_option] == 123
