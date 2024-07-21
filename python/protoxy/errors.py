import json
from dataclasses import dataclass
import typing

# related errors are nested in the json output. This is due to the miette design
# is is probably not well appropriate for a compiler output
# so we just flatten the related errors
def flatten_related(err):
    related = err.get("related", [])
    del err["related"]
    if err["message"] != "errors in multiple files":
        yield err
    for r in related:
        yield from flatten_related(r)

@dataclass
class Span:
    offset: int
    length: int

@dataclass
class Label:
    label: str
    span: Span

@dataclass
class DetailedError:
    """ A detailed error message, translated from the Rust implementation """
    message: str
    severity: str
    filename: str
    causes: typing.List[str]
    labels: typing.List[Label]
    def from_json(json):
        return DetailedError(
            message=json["message"],
            severity=json["severity"],
            filename=json.get("filename"),
            causes=json["causes"],
            labels=[Label(label=x["label"], span=Span(**x["span"])) for x in json.get("labels", [])]
        )

class ProtoxyError(Exception):
    """ Exception raised when there are errors in the compilation of the protobuf files """
    def __init__(self, message, details, json_details):
        Exception.__init__(self, message)
        self.details = details
        self.json_details = json_details

    def __repr__(self) -> str:
        return super().__repr__() + f"\n{self.details}"

    @property
    def all_errors(self):
        return [DetailedError.from_json(x) for x in flatten_related(json.loads(self.json_details))]
