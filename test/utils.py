import pytest
from google.protobuf import descriptor_pool as descriptor_pool
from google.protobuf.descriptor_pb2 import FileDescriptorProto

@pytest.fixture
def default_pool():
    """ fixture that adds the default google protobuf files to the descriptor pool 
    This is necessary to avoid tests to use the same default pool
    """
    pool = descriptor_pool.DescriptorPool()
    default = descriptor_pool.Default()
    for fn in [
        "google/protobuf/descriptor.proto",
        "google/protobuf/empty.proto",
        "google/protobuf/any.proto",
        "google/protobuf/wrappers.proto",
        "google/protobuf/timestamp.proto",
        "google/protobuf/duration.proto",
        "google/protobuf/field_mask.proto",
        "google/protobuf/struct.proto",        
    ]:
        try:
            desc = default.FindFileByName(fn)
            proto = FileDescriptorProto()
            desc.CopyToProto(proto)
            pool.Add(proto)
        except KeyError:
            pass
    saved_default = descriptor_pool.Default
    descriptor_pool.Default = lambda: pool
    yield pool  
    descriptor_pool.Default = saved_default