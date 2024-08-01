use protobuf::descriptor::{
        source_code_info::Location, DescriptorProto, EnumDescriptorProto, EnumValueDescriptorProto, FieldDescriptorProto, FileDescriptorProto, MethodDescriptorProto, OneofDescriptorProto, ServiceDescriptorProto
    };
use std::collections::VecDeque;
use super::tag;

#[derive(Debug)]
pub(crate) enum PathedDescriptor<'a> {
    Message(&'a mut DescriptorProto),
    Enum(&'a mut EnumDescriptorProto),
    Service(&'a mut ServiceDescriptorProto),
    Method(&'a mut MethodDescriptorProto),
    Field(&'a mut FieldDescriptorProto),
    EnumValue(&'a mut EnumValueDescriptorProto),
    Extension(&'a mut FieldDescriptorProto), // Assuming extensions are represented as FieldDescriptorProto
    Oneof(&'a mut OneofDescriptorProto),
}


pub(crate) trait PathedChilds {
    fn get_child_from_path(&mut self, path: &mut VecDeque<i32>) -> Option<PathedDescriptor>;
    fn get_child_from_loc(&mut self, loc: &Location) -> Option<PathedDescriptor> {
        let mut path: VecDeque<i32> = loc.path.iter().copied().collect();
        self.get_child_from_path(&mut path)
    }
}

impl PathedChilds for FileDescriptorProto {
    fn get_child_from_path(&mut self, path: &mut VecDeque<i32>) -> Option<PathedDescriptor> {
        let typ = path.pop_front()?;
        let idx = path.pop_front()? as usize;
        match typ {
            tag::file::MESSAGE_TYPE => {
                let message = self.message_type.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Message(message))
                } else {
                    message.get_child_from_path(path)
                }
            }
            tag::file::ENUM_TYPE => {
                let enum_ = self.enum_type.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Enum(enum_))
                } else {
                    enum_.get_child_from_path(path)
                }
            }
            tag::file::SERVICE => {
                let service = self.service.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Service(service))
                } else {
                    service.get_child_from_path(path)
                }
            }
            tag::file::EXTENSION => {
                let extension = self.extension.get_mut(idx)?;
                Some(PathedDescriptor::Extension(extension))
            }
            _ => None,
        }
    }
}

impl PathedChilds for ServiceDescriptorProto {
    fn get_child_from_path(&mut self, path: &mut VecDeque<i32>) -> Option<PathedDescriptor> {
        let typ = path.pop_front()?;
        let idx = path.pop_front()? as usize;
        match typ {
            tag::service::METHOD => {
                let method = self.method.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Method(method))
                } else {
                    None
                }
            }
            _ => None,
        }
    }
}

impl PathedChilds for EnumDescriptorProto {
    fn get_child_from_path(&mut self, path: &mut VecDeque<i32>) -> Option<PathedDescriptor> {
        let typ = path.pop_front()?;
        let idx = path.pop_front()? as usize;
        match typ {
            tag::enum_::VALUE => {
                let value = self.value.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::EnumValue(value))
                } else {
                    None
                }
            }
            _ => None,
        }
    }
}

impl PathedChilds for DescriptorProto {
    fn get_child_from_path(&mut self, path: &mut VecDeque<i32>) -> Option<PathedDescriptor> {
        let typ = path.pop_front()?;
        let idx = path.pop_front()? as usize;
        match typ {
            tag::message::FIELD => {
                let field = self.field.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Field(field))
                } else {
                    None
                }
            }
            tag::message::ENUM_TYPE => {
                let enum_ = self.enum_type.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Enum(enum_))
                } else {
                    enum_.get_child_from_path(path)
                }
            }
            tag::message::NESTED_TYPE => {
                let nested_type = self.nested_type.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Message(nested_type))
                } else {
                    nested_type.get_child_from_path(path)
                }
            }
            tag::message::ONEOF_DECL => {
                let oneof = self.oneof_decl.get_mut(idx)?;
                if path.is_empty() {
                    Some(PathedDescriptor::Oneof(oneof))
                } else {
                    None
                }
            }
            _ => None,
        }
    }
}