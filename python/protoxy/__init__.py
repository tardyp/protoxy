import typing
import os
from google.protobuf import descriptor_pool as descriptor_pool
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from ._protoxy import compile as _rs_compile, compile_python_modules

from .errors import ProtoxyError
from .importer import gen_modules

__all__ = ["compile", "compile_bin", "compile_as_modules", "ProtoxyError", "PathType"]

PathType = typing.Union[str, os.PathLike]

def _protoc_compile(
    files: typing.List[str],
    includes: typing.List[str] = [],
    include_source_info=True,
    include_imports=True,
) -> bytes:
    import subprocess
    import tempfile
    import shutil

    protoc = shutil.which("protoc")
    if not protoc:
        raise ValueError("protoc not found in PATH")
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "out")
        cmd = [protoc, "--descriptor_set_out=" + out]
        if include_source_info:
            cmd.append("--include_source_info")
        if include_imports:
            cmd.append("--include_imports")
        for inc in includes:
            cmd.append("-I" + inc)
        cmd.extend(files)
        try:
            subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            raise ValueError(
                "protoc failed with exit code "
                + str(e.returncode)
                + ": "
                + e.output.decode()
            )
        with open(out, "rb") as f:
            return f.read()

def normalize_inputs(files, includes):
    includes = [str(p) for p in includes]
    files = [str(p) for p in files]
    if not includes:
        includes = [os.path.dirname(files[0])]
    return files, includes

def compile_bin(
    files: typing.List[PathType],
    includes: typing.List[PathType] = [],
    include_imports=True,
    include_source_info=True,
    use_protoc=False,
    comments2option=None,
) -> bytes:
    """
    Compiles a set of protobuf files using the given include paths.

    :param includes: List of include paths (can be strings or `os.PathLike` objects)
    :param files: List of files to compile (can be strings or `os.PathLike` objects)
    :param include_imports: Sets whether the output `FileDescriptorSet` should include imported files.
     only files explicitly included in `files` are included. If this option is set, imported files are included too.
    :param include_source_info: Include source info in the output (this includes comments found in the source files)
    :param use_protoc: Use the `protoc` binary to compile the files. If this is set to `False`, the Rust implementation
    :param comments2option: A dictionary mapping comments to protobuf options. The keys are the name of the protobuf object:
    (file, message, enum, service, method, field, enum_value, extension, oneof) and the values are the option numeric id.
    This is only supported by the Rust implementation

    :return: The compiled `FileDescriptorSet` as a binary string

    :raises: `ValueError` if the compilation fails
    """
    files, includes = normalize_inputs(files, includes)
    if use_protoc:
        return _protoc_compile(files, includes, include_source_info, include_imports)
    else:
        return _rs_compile(files, includes, include_source_info, include_imports, comments2option)


def compile(
    files: typing.List[PathType],
    includes: typing.List[PathType] = [],
    include_imports=True,
    include_source_info=True,
    use_protoc=False,
    comments2option=None,
) -> FileDescriptorSet:
    """
    Compiles a set of protobuf files using the given include paths.
    :param includes: List of include paths (can be strings or `os.PathLike` objects)
    :param files: List of files to compile (can be strings or `os.PathLike` objects)
    :param include_imports: Sets whether the output `FileDescriptorSet` should include imported files.
     only files explicitly included in `files` are included. If this option is set, imported files are included too.
    :param include_source_info: Include source info in the output (this includes comments found in the source files)
    :param use_protoc: Use the `protoc` binary to compile the files. If this is set to `False`, the Rust implementation
    :param comments2option: A dictionary mapping comments to protobuf options. The keys are the name of the protobuf object:
    (file, message, enum, service, method, field, enum_value, extension, oneof) and the values are the option numeric id.

    :return: The compiled `FileDescriptorSet` object
    :raises: `ValueError` if the compilation fails
    """
    bin = compile_bin(files, includes, include_imports, include_source_info, use_protoc, comments2option)
    fds = FileDescriptorSet()
    fds.ParseFromString(bin)
    return fds

def compile_as_packages(
    files: typing.List[PathType],
    includes: typing.List[PathType] = [],
    dest: typing.Optional[dict] = None,
    module_parent="protoxy",
) -> FileDescriptorSet:
    """
    Compiles protobuf files as python packages using the given include paths.

    :param files: The files to compile
    :param includes: List of include paths (can be strings or `os.PathLike` objects)
    :param dest: A dictionary to store the compiled modules (meant to be globals()). If not set, a new dictionary is created
    :param module_suffix: The suffix to use for the generated modules. Default is ''. use `_pb2` for compatibility with protoc

    :return: a module object compiled from the given files, similar to the _pb2.py files generated by protoc
    :raises: `ValueError` if the compilation fails
    """
    if dest is None:
        dest = dict()
    files, includes = normalize_inputs(files, includes)
    gen_modules(compile_python_modules(files, includes), dest, module_parent)
    return dest

class ProtoxyModule(object):
    def __repr__(self) -> str:
        ret = "<ProtoxyModule: \n"
        for k, v in self.__dict__.items():
            v = repr(v).replace("\n", "\n  ")
            ret += f"{k}={v}\n"
        return ret + ">"


def compile_as_modules(
    files: typing.List[PathType],
    includes: typing.List[PathType] = [],
    dest: typing.Optional[dict] = None,
    use_protoc=False,
    module_suffix="",
) -> FileDescriptorSet:
    """
    Compiles a protobuf module using the given include paths.

    :param files: The files to compile
    :param includes: List of include paths (can be strings or `os.PathLike` objects)
    :param use_protoc: Use the `protoc` binary to compile the files. If this is set to `False`, the Rust implementation
    :param dest: A dictionary to store the compiled modules (meant to be globals()). If not set, a new dictionary is created
    :param module_suffix: The suffix to use for the generated modules. Default is ''. use `_pb2` for compatibility with protoc

    :return: a module object compiled from the given files, similar to the _pb2.py files generated by protoc
    :raises: `ValueError` if the compilation fails
    """
    from google.protobuf.internal import builder as _builder

    if dest is None:
        dest = dict()
    files, includes = normalize_inputs(files, includes)
    mods = compile_python_modules(files, includes)
    pool = descriptor_pool.Default()
    for m in mods:
        module_name = os.path.basename(m.name).replace(".proto", module_suffix)
        DESCRIPTOR = pool.AddSerializedFile(m.fd)
        _globals = dict()
        _builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
        _builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, module_name, _globals)
        mod = ProtoxyModule()
        mod.__name__ = module_name
        mod.__dict__.update(_globals)
        dest[module_name] = mod
    return dest
