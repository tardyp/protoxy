use std::collections::HashMap;

use miette::Diagnostic;
use protobuf::{descriptor::FileDescriptorSet, Message};
use pyo3::{prelude::*, types::PyBytes};
use thiserror::Error;
mod comments2option;
mod path_resolver;
mod typing_stub;

#[derive(Debug, Error, Diagnostic)]
#[error("errors in multiple files")]
struct AllErrors {
    #[related]
    all: Vec<protox::Error>,
}
mod error {
    use miette::JSONReportHandler;
    use pyo3::PyErr;

    pyo3::import_exception!(protoxy, ProtoxyError);
    pub(super) fn into_pyerr(err: miette::Error) -> PyErr {
        let mut json = String::new();
        JSONReportHandler::new()
            .render_report(&mut json, err.as_ref())
            .unwrap();

        ProtoxyError::new_err((err.to_string(), format!("{:?}", err), json))
    }
}

fn _compile(
    files: Vec<String>,
    includes: Vec<String>,
    include_source_info: bool,
    include_imports: bool,
) -> miette::Result<Vec<u8>> {
    let files = files.iter().map(|f| f.as_str());
    let includes = includes.iter().map(|i| i.as_str());
    let mut c = protox::Compiler::new(includes)?;
    let mut all_errors = Vec::new();
    c.include_source_info(include_source_info);
    c.include_imports(include_imports);
    for file in files {
        if let Err(e) = c.open_file(file) {
            all_errors.push(e);
        }
    }
    if all_errors.is_empty() {
        Ok(c.encode_file_descriptor_set())
    } else {
        if all_errors.len() == 1 {
            return Err(all_errors.pop().unwrap().into());
        }
        Err(AllErrors { all: all_errors }.into())
    }
}

#[pyfunction]
#[pyo3(signature = (files, includes, include_source_info, include_imports, comments2option=None))]
fn compile<'py>(
    py: Python<'py>,
    files: Vec<String>,
    includes: Vec<String>,
    include_source_info: bool,
    include_imports: bool,
    comments2option: Option<HashMap<String, u32>>,
) -> PyResult<Bound<'py, PyBytes>> {
    let mut res = _compile(files, includes, include_source_info, include_imports)
        .map_err(error::into_pyerr)?;
    if let Some(comments2option) = comments2option {
        let ids = comments2option
            .iter()
            .fold(comments2option::DescriptionIds::default(), |mut ids, (k, v)| {
                match k.as_str() {
                    "file" => ids.file = Some(*v),
                    "message" => ids.message = Some(*v),
                    "enum" => ids.enum_ = Some(*v),
                    "service" => ids.service = Some(*v),
                    "method" => ids.method = Some(*v),
                    "field" => ids.field = Some(*v),
                    "enum_value" => ids.enum_value = Some(*v),
                    "extension" => ids.extension = Some(*v),
                    "oneof" => ids.oneof = Some(*v),
                    _ => {}
                }
                ids
            });
        res = comments2option::comments2option(&res, &ids);
    }
    Ok(PyBytes::new_bound(py, &res))
}

#[pyclass]
pub struct PythonProtoxyModule {
    pub fd: Vec<u8>,
    #[pyo3(get)]
    pub typing_stub: String,
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub package: String,
    #[pyo3(get)]
    pub dep_names: Vec<String>,
}

#[pymethods]
impl PythonProtoxyModule {
    #[getter]
    fn fd<'py>(&'py self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        Ok(PyBytes::new_bound(py, self.fd.as_slice()))
    }
}
#[pyfunction]
#[pyo3(signature = (files, includes))]
fn compile_python_modules(
    files: Vec<String>,
    includes: Vec<String>,
) -> PyResult<Vec<PythonProtoxyModule>> {
    let fds = _compile(files, includes, true, true)
        .map_err(error::into_pyerr)?;

    let fds = FileDescriptorSet::parse_from_bytes(&fds).unwrap();
    let mut res = Vec::new();

    let package_by_file = fds.file.iter().map(|fd| {
        let package = fd.package.clone().unwrap();
        (fd.name.clone().unwrap(), package)
    }).collect::<HashMap<String, String>>();

    for mut fd in fds.file {
        if fd.package == Some("google.protobuf".to_string()) {
            continue;
        }
        let typing_stub = typing_stub::generate_typing_stub(&fd);
        // source info is not needed in the output, but for stub generation
        fd.source_code_info.clear();
        let mut dep_names = Vec::new();
        for dep in fd.dependency.iter() {
            if let Some(dep) = package_by_file.get(dep) {
                dep_names.push(dep.to_owned());
            }
        }
        res.push(PythonProtoxyModule {
            fd: fd.write_to_bytes().unwrap(),
            typing_stub,
            package: fd.package.unwrap(),
            name: fd.name.unwrap(),
            dep_names,
        });
    }
    Ok(res)
}

#[pymodule]
fn _protoxy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compile, m)?)?;
    m.add_function(wrap_pyfunction!(compile_python_modules, m)?)?;
    Ok(())
}

