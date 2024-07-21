[![pypi](https://img.shields.io/pypi/v/protoxy.svg)](https://pypi.org/project/protoxy)
[![Continuous integration](https://github.com/tardyp/protoxy/actions/workflows/CI.yml/badge.svg)](https://github.com/tardyp/protoxy/actions/workflows/CI.yml)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)

# protoxy

A compiler for .proto files into FileDescriptorSets or (experimentally) python dynamic module.
Python bindings for the [protox](https://github.com/andrewhickman/protox) rust library.

# Installation

```bash
pip install protoxy
```

# Usage

```python
import protoxy

# Compile a proto file (returns a FileDescriptorSets object using the protobuf library)
fds = protoxy.compile(["path/to/file.proto"])

# Compile a proto file (returns a binary FileDescriptorSets object)
fds_bin = protoxy.compile_bin(["path/to/file.proto"])

# Compile a proto file into a dynamic python modules, injected into your globals
protoxy.compile_as_modules(["path/to/file.proto"], dest=globals())

# The returned module is similar to the one generated by protoc
# you can keep protoc _pb2 suffix by setting suffix='_pb2'
file.Message()
```

See the tests for more examples.

# Additional options

All those apis have additional options that can be passed as keyword arguments.

```python

fds = protoxy.compile(
    files = ["path/to/file.proto"],
    includes = ["path/to"],
    include_imports = True,
    include_source_info = True,
    use_protoc = False)
```

- files: List of files to compile (can be strings or `os.PathLike` objects)

- includes: List of include paths (can be strings or `os.PathLike` objects), if empty, defaults to the directory path of the first file in `files`

- include_imports: Sets whether the output `FileDescriptorSet` should include imported files.
  only files explicitly included in `files` are included. If this option is set, imported files are included too.

- include_source_info: Include source info in the output (this includes comments found in the source files)

- use_protoc: Use the `protoc` binary to compile the files. If this is set to `True`, the protoc implementation is used using binary found in $PATH. protoc is defacto standard implementation of the protobuf compiler, but using it with python requires to run another binary, which can be a problem in some environments, is slower than the rust implementation and has scalability issue with command line length on windows.

# Error handling

The library raises a `protoxy.ProtoxyError` exception when an error occurs during the compilation.

* short description of the error can be found in the `message` attribute of the exception.

* long description of the error can be found in the `details` attribute of the exception (or `repr(e)`).

* machine readable list of all errors can be found in the `all_errors: typing.List[protoxy.errors.DetailedError]` property of the exception.

It will be formatted using the rust `miette` library, which is a bit more user friendly than the protobuf error messages.

Details contain all errors for the whole compilation.

Example of details:
```
Error:   × name 'strings' is not defined
   ╭─[test.proto:5:9]
 4 │     message Test {
 5 │         strings name = 1;
   ·         ───┬───
   ·            ╰── found here
 6 │         fold name2 = 2;
   ╰────

Error:   × name 'fold' is not defined
   ╭─[test.proto:6:9]
 5 │         strings name = 1;
 6 │         fold name2 = 2;
   ·         ──┬─
   ·           ╰── found here
 7 │     }
   ╰────
Error:   × expected an integer, but found '='
   ╭─[test2.proto:6:21]
 5 │         strings name = 1;
 6 │         fold name2 == 2;
   ·                     ┬
   ·                     ╰── found here
 7 │     }
   ╰────```

# proto module best practice

Structure of a python project can be made like this:

```
project/
    protos/
        file1.proto
        file2.proto
    protos.py
    main.py
```

Following python module shall be named protos.py and contain the following code:

```python
import pathlib, protoxy

_protos = (pathlib.Path(__file__).parent / "protos").glob("*.proto")
protoxy.compile_as_modules(_protos, dest=globals())

```