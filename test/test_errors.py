import protoxy
import pytest
from .utils import *  # noqa


def test_basic(tmp_path, default_pool):
    test_proto = tmp_path.joinpath("test.proto")
    test_proto.write_text("""
    syntax = "proto3";
    package test;
    message Test {
        strings name = 1;
    }
    """)
    with pytest.raises(protoxy.ProtoxyError) as excinfo:
        protoxy.compile([test_proto])
    assert "name 'strings' is not defined" == str(excinfo.value)
    assert "name 'strings' is not defined" in excinfo.value.details
    assert "test.proto" in excinfo.value.details
    assert "5:9" in excinfo.value.details


def test_notfound(tmp_path, default_pool):
    test_proto = tmp_path.joinpath("test.proto")
    with pytest.raises(protoxy.ProtoxyError) as excinfo:
        protoxy.compile([test_proto])
    assert "test.proto' is not in any include path" in str(excinfo.value)


@pytest.mark.xfail(
    reason="This test fails on some systems because of chmod", strict=False
)
def test_notreadable(tmp_path, default_pool):
    test_proto = tmp_path.joinpath("test.proto")
    test_proto.touch()
    test_proto.chmod(0o000)
    with pytest.raises(protoxy.ProtoxyError) as excinfo:
        protoxy.compile([test_proto])
    assert "error opening file" in str(excinfo.value)
    assert "Permission denied" in repr(excinfo.value)


def test_multiple(tmp_path, default_pool):
    test_proto = tmp_path.joinpath("test.proto")
    # first file is typing error
    test_proto.write_text("""
    syntax = "proto3";
    package test;
    message Test {
        strings name = 1;
        fold name2 = 2;
    }
    """)
    test2_proto = tmp_path.joinpath("test2.proto")
    # second file is syntax error
    test2_proto.write_text("""
    syntax = "proto3";
    package test;
    message Test2 {
        string name = 1;
    }
    """)
    with pytest.raises(protoxy.ProtoxyError) as excinfo:
        protoxy.compile([test_proto, test2_proto])
    # str is first error when only one file is error
    assert "name 'strings' is not defined" == str(excinfo.value)
    # repr contains all errors
    all = repr(excinfo.value)
    assert "name 'strings' is not defined" in all
    assert "name 'fold' is not defined" in all


def test_multiple_files(tmp_path, default_pool):
    test_proto = tmp_path.joinpath("test.proto")
    # first file is typing error
    test_proto.write_text("""
    syntax = "proto3";
    package test;
    message Test {
        strings name = 1;
        fold name2 = 2;
    }
    """)
    test2_proto = tmp_path.joinpath("test2.proto")
    # second file is syntax error
    test2_proto.write_text("""
    syntax = "proto3";
    package test;
    message Test2 {
        strings name = 1;
        fold name2 == 2;
    }
    """)
    with pytest.raises(protoxy.ProtoxyError) as excinfo:
        protoxy.compile([test_proto, test2_proto])

    # as there are multiple files, str will not report the first error
    assert "errors in multiple files" == str(excinfo.value)
    # repr contains all errors
    all = repr(excinfo.value)
    assert "name 'strings' is not defined" in all
    assert "name 'fold' is not defined" in all
    assert "expected an integer, but found '='" in all
    assert (
        excinfo.value.all_errors
        == [
            {
                "message": "name 'strings' is not defined",
                "severity": "error",
                "causes": [],
                "filename": "test.proto",
                "labels": [
                    {"label": "found here", "span": {"offset": 69, "length": 7}}
                ],
            },
            {
                "message": "name 'fold' is not defined",
                "severity": "error",
                "causes": [],
                "filename": "test.proto",
                "labels": [
                    {"label": "found here", "span": {"offset": 95, "length": 4}}
                ],
            },
            {
                "message": "expected an integer, but found '='",
                "severity": "error",
                "causes": [],
                "filename": "test2.proto",
                "labels": [
                    {"label": "found here", "span": {"offset": 108, "length": 1}}
                ],
            },
        ]
    )