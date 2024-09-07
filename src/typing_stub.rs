use protobuf::descriptor::{DescriptorProto, EnumDescriptorProto, FileDescriptorProto, ServiceDescriptorProto};
use heck::{AsUpperCamelCase, AsSnakeCase, AsShoutySnakeCase};

/// Generate typing stub for a given file descriptor
/// this stub can be parsed by mypy or pylance to get `type information
/// the generated stub is indented with 4 spaces, as it is meant to be prefixed by "if TYPE_CHECKING:<stub>else: <dynamic upb generated code>"
pub(crate) fn generate_typing_stub(fds: &FileDescriptorProto) -> String {
    let mut res = String::new();
    for message in fds.message_type.iter() {
        res.push_str(&generate_message_typing_stub(message, 1));
    }
    for enum_ in fds.enum_type.iter() {
        res.push_str(&generate_enum_typing_stub(enum_, 1));
    }
    for service in fds.service.iter() {
        res.push_str(&generate_service_typing_stub(service, 1));
    }
    res
}
fn generate_message_typing_stub(message: &DescriptorProto, indent: usize) -> String {
    let mut res = String::new();
    res.push_str(&format!(
        "{}class {}:\n",
        "    ".repeat(indent),
        AsUpperCamelCase(message.name())
    ));
    if message.field.is_empty() {
        res.push_str(&format!("{}pass\n", "    ".repeat(indent + 1)));
    } else {
        for field in message.field.iter() {
            res.push_str(&format!(
                "{}{}: {}\n",
                "    ".repeat(indent + 1),
                AsSnakeCase(field.name()),
                "Any" // generate_field_typing_stub(field)
            ));
        }
    }
    for nested in message.nested_type.iter() {
        res.push_str(&generate_message_typing_stub(nested, indent + 1));
    }
    res
}
fn generate_enum_typing_stub(enum_: &EnumDescriptorProto, indent: usize) -> String {
    let mut res = String::new();
    res.push_str(&format!(
        "{}class {}:\n",
        "    ".repeat(indent),
        AsUpperCamelCase(enum_.name())
    ));
    if enum_.value.is_empty() {
        res.push_str(&format!("{}pass\n", "    ".repeat(indent + 1)));
    } else {
        for value in enum_.value.iter() {
            res.push_str(&format!(
                "{}{} = {}\n",
                "    ".repeat(indent + 1),
                AsShoutySnakeCase(value.name()),
                value.number()
            ));
        }
    }
    res
}
fn generate_service_typing_stub(service: &ServiceDescriptorProto, indent: usize) -> String {
    let mut res = String::new();
    res.push_str(&format!(
        "{}class {}:",
        "    ".repeat(indent),
        AsUpperCamelCase(service.name())
    ));
    if service.method.is_empty() {
        res.push_str("\n");
    } else {
        res.push_str(":\n");
        for method in service.method.iter() {
            res.push_str(&format!(
                "{}def {}(self, request: Any) -> Any:\n",
                "    ".repeat(indent + 1),
                AsSnakeCase(method.name())
            ));
        }
    }
    res
}

