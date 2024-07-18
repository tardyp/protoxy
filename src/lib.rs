use pyo3::{prelude::*, types::PyBytes};


fn _compile(
    files: Vec<String>, includes: Vec<String>,
    include_source_info: bool, include_imports: bool
) -> Result<Vec<u8>, protox::Error> {
    let files = files.iter().map(|f| f.as_str());
    let includes = includes.iter().map(|i| i.as_str());
    Ok(protox::Compiler::new(includes)?
        .include_source_info(include_source_info)
        .include_imports(include_imports)
        .open_files(files)?
        .encode_file_descriptor_set())
}

#[pyfunction]
fn compile<'py>(py: Python<'py>, files: Vec<String>, includes: Vec<String>,
    include_source_info: bool, include_imports: bool
    ) -> PyResult<Bound<'py, PyBytes>> {
    let res = _compile(files, includes, include_source_info, include_imports)
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    Ok(PyBytes::new_bound(py, &res))
}

#[pymodule]
fn _protoxy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compile, m)?)?;
    Ok(())
}
