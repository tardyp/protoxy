import typing
import os
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from ._protoxy import compile as rs_compile

PathType = typing.Union[str, os.PathLike]


def compile_bin(includes: typing.List[PathType], 
            files: typing.List[PathType],
            include_imports=True,
            include_source_info=True) -> bytes:
    """
    Compiles a set of protobuf files using the given include paths.

    :param includes: List of include paths (can be strings or `os.PathLike` objects)
    :param files: List of files to compile (can be strings or `os.PathLike` objects)
    :param include_imports: Sets whether the output `FileDescriptorSet` should include imported files.
     only files explicitly included in `files` are included. If this option is set, imported files are included too.
    :param include_source_info: Include source info in the output (this includes comments found in the source files)

    :return: The compiled `FileDescriptorSet` as a binary string

    :raises: `ValueError` if the compilation fails
    """
    includes = [str(p) for p in includes]
    files = [str(p) for p in files]
    return rs_compile(includes, files, include_imports, include_source_info)


def compile(includes: typing.List[PathType], 
            files: typing.List[PathType],
            include_imports=True,
            include_source_info=True) -> FileDescriptorSet:
    """
    Compiles a set of protobuf files using the given include paths.
    :param includes: List of include paths (can be strings or `os.PathLike` objects)
    :param files: List of files to compile (can be strings or `os.PathLike` objects)
    :param include_imports: Sets whether the output `FileDescriptorSet` should include imported files.
     only files explicitly included in `files` are included. If this option is set, imported files are included too.
    :param include_source_info: Include source info in the output (this includes comments found in the source files)
    
    :return: The compiled `FileDescriptorSet` object
    :raises: `ValueError` if the compilation fails
    """
    bin = compile_bin(includes, files, include_imports, include_source_info)
    fds = FileDescriptorSet()
    fds.ParseFromString(bin)
    return fds
