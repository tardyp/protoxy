import protoxy
from .utils import * #noqa
from google.protobuf import descriptor_pool as descriptor_pool


def test_basic(tmp_path):
    test_proto = tmp_path.joinpath("test.proto")
    test_proto.write_text("""
    syntax = "proto3";
    import "google/protobuf/descriptor.proto";
    package test_comments;
    extend google.protobuf.MessageOptions {
        string doc = 10000;
    }
    extend google.protobuf.FieldOptions {
        string field_doc = 10000;
    }

    // Documentation for Test
    message Test {
        // Documentation for name
        string name = 1;
    }
    """)
    mod = protoxy.compile_as_modules([test_proto])
    doc_option = mod["test"].doc
    field_doc_option = mod["test"].field_doc

    fds = protoxy.compile([test_proto], comments2option={"message": 10000, "field": 10000})
    assert fds.file[1].name == "test.proto"
    assert fds.file[1].message_type[0].options.Extensions[doc_option] == "Documentation for Test"
    assert fds.file[1].message_type[0].field[0].options.Extensions[field_doc_option] == "Documentation for name"

