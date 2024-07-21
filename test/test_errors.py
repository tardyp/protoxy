import protoxy
import pytest
from .utils import * #noqa

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

def test_notreadable(tmp_path, default_pool):
    test_proto = tmp_path.joinpath("test.proto")
    test_proto.touch()
    test_proto.chmod(0o000)
    with pytest.raises(protoxy.ProtoxyError) as excinfo:
        protoxy.compile([test_proto])
    assert "error opening file" in str(excinfo.value)
    assert "Permission denied" in repr(excinfo.value)