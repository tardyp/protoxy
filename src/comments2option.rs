use crate::path_resolver::protobuf::{PathedChilds, PathedDescriptor};
use protobuf::{descriptor::FileDescriptorSet, Message};

#[derive(Debug, Default)]
pub struct DescriptionIds {
    pub file: Option<u32>,
    pub message: Option<u32>,
    pub enum_: Option<u32>,
    pub service: Option<u32>,
    pub method: Option<u32>,
    pub field: Option<u32>,
    pub enum_value: Option<u32>,
    pub extension: Option<u32>,
    pub oneof: Option<u32>,
}
pub fn comments2option(res: &[u8], ids: &DescriptionIds) -> Vec<u8> {
    let mut res = FileDescriptorSet::parse_from_bytes(res).unwrap();
    for file in &mut res.file {
        if file.name().starts_with("google") {
            continue;
        }
        let sci = file.source_code_info.clone();
        for loc in sci.location.iter() {
            let comments = if loc.has_leading_comments() {
                loc.leading_comments.as_ref().unwrap().clone()
            } else if loc.has_trailing_comments() {
                loc.trailing_comments.as_ref().unwrap().clone()
            } else {
                continue;
            };
            let comments = comments.trim().to_string();
            if let Some(pathed) = file.get_child_from_loc(loc) {
                insert_comment(pathed, comments, ids);
            }
        }
    }
    res.write_to_bytes().unwrap()
}
macro_rules! insert_comment {
    ($x: ident, $comment: ident, $id: expr) => {
        if let Some(id) = $id {
            $x.options
                .mut_or_insert_default()
                .special_fields
                .mut_unknown_fields()
                .add_length_delimited(id, $comment);
        }
    };
}
fn insert_comment(pathed: PathedDescriptor, comment: String, ids: &DescriptionIds) {
    let comment = comment.as_bytes().to_vec();
    match pathed {
        PathedDescriptor::Message(message) => {
            insert_comment!(message, comment, ids.message);
        }
        PathedDescriptor::Enum(enum_) => {
            insert_comment!(enum_, comment, ids.enum_);
        }
        PathedDescriptor::Service(service) => {
            insert_comment!(service, comment, ids.service);
        }
        PathedDescriptor::Method(method) => {
            insert_comment!(method, comment, ids.method);
        }
        PathedDescriptor::Field(field) => {
            insert_comment!(field, comment, ids.field);
        }
        PathedDescriptor::EnumValue(enum_value) => {
            insert_comment!(enum_value, comment, ids.enum_value);
        }
        PathedDescriptor::Extension(extension) => {
            insert_comment!(extension, comment, ids.extension);
        }
        PathedDescriptor::Oneof(oneof) => {
            insert_comment!(oneof, comment, ids.oneof);
        }
    }
}

