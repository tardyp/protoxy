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
- comments2option: A dictionary mapping comments to protobuf options. The keys are the name of the protobuf object: ("file", "message", "enum", "service", "method", "field", "enum_value", "extension", "oneof") and the values are the option numeric id. This is only supported by the Rust implementation.
Convert comments to options. This is useful to include documentation in the generated python module. See the comments2option section for more details.

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

# Comments2option

Protobuf support for documentation is limited to comments, which are included in source code info, an obscure part of FileDescriptor.
Sourcecode info is hard to use because it relies on object paths, which are described using id and index in the protobuf object tree.
This is only described in the protobuf mailing list in a message from Jerry Berg in a thread called "Best way to parse SourceCodeInfo Data From Protobuf Files"

https://groups.google.com/g/protobuf/c/AyOQvhtwvYc/m/AtgdNNkbCAAJ (not sure if this URL is stable)


It is much easier to process if the documentation is included as a protobuf option for each message, field, enum, etc. But the syntax is not ideal, as the options strings must be split across line boundary e.g

```proto
syntax = "proto3";
import "doc.proto";
message Test {
  option (doc.message_description) = "This is a test message "
  "whose doc is split between"
  "multiple lines";
  string name = 1 [(doc.field_description) = "This is a test field"];
}
```

doc.proto being:

```proto
syntax = "proto3";
package doc;
extend google.protobuf.MessageOptions {
  string message_description = 50000;
}
extend google.protobuf.FieldOptions {
  string field_description = 50001;
}
```
Notice how the option is split between multiple lines. It is easy to forget to add the trailing space (like in second line), which will result in some word being concatenated.

To avoid this, the `comments2option` parameter of the protoxy compiler can be used to convert comments into options. It will add the option to the next element, so the above example can be written as:

```proto
syntax = "proto3";
import "doc.proto";
// This is a test message whose doc is
// split between multiple lines
message Test {
  // This is a test field
  string name = 1;
}
```
in your python code, you can then use:
```python
import protoxy

mod = protoxy.compile_as_modules(
    files = ["path/to/doc.proto"],
    includes = ["path/to"])

# for python's protobuf module to properly decode the options,
# they must be loaded as a python module first
message_description = mod["doc"].message_description
field_description = mod["doc"].field_description

fds = protoxy.compile(
    files = ["path/to/file.proto"],
    includes = ["path/to"],
    include_source_info = True,
    comments2option = {"message": 50000, "field": 50001})

assert fds.file[0].message_type[0].options.Extensions[message_description] == "This is a test message whose doc is split between multiple lines"
```