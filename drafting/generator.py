from __future__ import annotations

import re
import xml.sax.saxutils as xml_utils
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple
from zipfile import ZipFile

ALLOWED_TONES = {"firm", "neutral", "conciliatory"}

TONE_PROFILES: Dict[str, Dict[str, str]] = {
    "firm": {
        "greeting": "Hello",
        "purpose": "This correspondence seeks prompt and complete attention to the issues outlined below.",
        "closing": "Thank you for your immediate attention to this matter.",
    },
    "neutral": {
        "greeting": "Hello",
        "purpose": "I am providing the following details to ensure the record is clear and accurate.",
        "closing": "Thank you for your time and review.",
    },
    "conciliatory": {
        "greeting": "Hello",
        "purpose": "I appreciate your consideration and collaboration in resolving the points below.",
        "closing": "Thank you for working together on this.",
    },
}

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>
"""

TOKEN_RE = re.compile(r"({{.*?}}|{%.*?%})", re.DOTALL)
DEFAULT_RE = re.compile(r'^(?P<path>[\w\.]+)(\|default\("(?P<default>.*?)"\))?$')


class MissingFieldsError(ValueError):
    """Raised when required fields for a template are missing."""

    def __init__(self, missing_fields: Iterable[str]):
        self.missing_fields = sorted(set(missing_fields))
        joined = ", ".join(self.missing_fields)
        super().__init__(f"Missing required fields: {joined}")


def resolve_path(context: Mapping[str, Any], path: str) -> Any:
    """Resolve dotted paths within the context mapping."""
    current: Any = context
    for segment in path.split("."):
        if isinstance(current, Mapping):
            current = current.get(segment)
        else:
            current = getattr(current, segment, None)
        if current is None:
            break
    return current


class Node:
    def render(self, context: Mapping[str, Any]) -> str:
        raise NotImplementedError


class TextNode(Node):
    def __init__(self, text: str):
        self.text = text

    def render(self, context: Mapping[str, Any]) -> str:  # noqa: ARG002
        return self.text


class VariableNode(Node):
    def __init__(self, expression: str):
        match = DEFAULT_RE.match(expression)
        if not match:
            raise ValueError(f"Unsupported variable expression: {expression}")
        self.path = match.group("path")
        self.default = match.group("default")

    def render(self, context: Mapping[str, Any]) -> str:
        value = resolve_path(context, self.path)
        if (value is None or value == "") and self.default is not None:
            value = self.default
        return "" if value is None else str(value)


class ForNode(Node):
    def __init__(self, item_name: str, iterable_name: str, body: List[Node], else_body: List[Node]):
        self.item_name = item_name
        self.iterable_name = iterable_name
        self.body = body
        self.else_body = else_body

    def render(self, context: Mapping[str, Any]) -> str:
        iterable = resolve_path(context, self.iterable_name) or []
        output: List[str] = []
        if iterable:
            for item in iterable:
                loop_context = dict(context)
                loop_context[self.item_name] = item
                output.append("".join(node.render(loop_context) for node in self.body))
        else:
            output.append("".join(node.render(context) for node in self.else_body))
        return "".join(output)


def parse_template(text: str) -> List[Node]:
    tokens = TOKEN_RE.split(text)
    nodes, index = _parse_tokens(tokens, 0, set())
    if index != len(tokens):
        raise ValueError("Template parsing did not consume all tokens.")
    return nodes


def _parse_tokens(tokens: List[str], index: int, stop_tags: set[str]) -> Tuple[List[Node], int]:
    nodes: List[Node] = []
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("{%"):
            tag = token[2:-2].strip()
            if tag in stop_tags:
                return nodes, index
            if tag.startswith("for "):
                parts = tag.split()
                if len(parts) != 4 or parts[2] != "in":
                    raise ValueError(f"Malformed for tag: {tag}")
                item_name, iterable_name = parts[1], parts[3]
                body, index = _parse_tokens(tokens, index + 1, {"else", "endfor"})
                else_body: List[Node] = []
                if index < len(tokens):
                    possible_else = tokens[index]
                    if possible_else.startswith("{%") and possible_else[2:-2].strip() == "else":
                        else_body, index = _parse_tokens(tokens, index + 1, {"endfor"})
                if index >= len(tokens) or tokens[index][2:-2].strip() != "endfor":
                    raise ValueError("Unclosed for tag in template.")
                index += 1
                nodes.append(ForNode(item_name, iterable_name, body, else_body))
                continue
            raise ValueError(f"Unsupported tag '{tag}' in template.")
        if token.startswith("{{"):
            nodes.append(VariableNode(token[2:-2].strip()))
        elif token:
            nodes.append(TextNode(token))
        index += 1
    return nodes, index


class MiniTemplate:
    """Minimal renderer supporting the subset of Jinja used in templates."""

    def __init__(self, text: str):
        self.nodes = parse_template(text)

    def render(self, context: Mapping[str, Any]) -> str:
        return "".join(node.render(context) for node in self.nodes)


@dataclass
class DraftInputs:
    """Inputs needed to render a template."""

    facts: Sequence[str] = field(default_factory=list)
    insights: Sequence[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tone: str = "neutral"


class TemplateGenerator:
    """Loads and renders drafting templates with validation and export helpers."""

    def __init__(self, template_dir: Path):
        self.template_dir = Path(template_dir)
        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")

        self.required_fields = {
            "appeal_letter.j2": {"case_id", "claimant_name", "requested_action", "signature"},
            "evidence_request.j2": {"case_id", "documents_requested", "context_summary", "signature"},
            "deadline_reminder.j2": {"deadline", "signature"},
        }
        self.template_cache: Dict[str, MiniTemplate] = {}

    def _normalize_template_name(self, template_name: str) -> str:
        normalized = template_name
        if not normalized.endswith(".j2"):
            normalized = f"{normalized}.j2"
        return normalized

    def _validate_required_fields(self, template_name: str, context: Mapping[str, Any]) -> None:
        required = self.required_fields.get(template_name, set())
        missing = {field for field in required if not context.get(field)}
        if missing:
            raise MissingFieldsError(missing)

    def _tone_profile(self, tone: str) -> Dict[str, str]:
        if tone not in ALLOWED_TONES:
            raise ValueError(f"Unsupported tone '{tone}'. Choose from {sorted(ALLOWED_TONES)}.")
        return TONE_PROFILES[tone]

    def build_context(self, inputs: DraftInputs) -> Dict[str, Any]:
        context: Dict[str, Any] = dict(inputs.metadata)
        context.update(
            {
                "facts": list(inputs.facts),
                "insights": list(inputs.insights),
                "tone": inputs.tone,
                "tone_profile": self._tone_profile(inputs.tone),
            }
        )
        return context

    def _load_template(self, template_name: str) -> MiniTemplate:
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        path = self.template_dir / template_name
        if not path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found in {self.template_dir}")
        content = path.read_text()
        template = MiniTemplate(content)
        self.template_cache[template_name] = template
        return template

    def generate(self, template_name: str, inputs: DraftInputs) -> str:
        normalized_name = self._normalize_template_name(template_name)
        template = self._load_template(normalized_name)
        context = self.build_context(inputs)
        self._validate_required_fields(normalized_name, context)
        return template.render(context)

    def export(self, rendered_text: str, output_path: Path, fmt: str = "txt", metadata: Mapping[str, Any] | None = None) -> Path:
        fmt = fmt.lower()
        metadata = metadata or {}
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "txt":
            output_path.write_text(rendered_text)
        elif fmt == "eml":
            self._write_eml(rendered_text, output_path, metadata)
        elif fmt == "docx":
            self._write_docx(rendered_text, output_path, metadata.get("subject"))
        else:
            raise ValueError("Unsupported export format. Choose from txt, eml, or docx.")
        return output_path

    def _write_eml(self, body: str, output_path: Path, metadata: Mapping[str, Any]) -> None:
        message = EmailMessage()
        message["Subject"] = metadata.get("subject") or f"Draft: {output_path.stem}"
        if metadata.get("from_address"):
            message["From"] = metadata["from_address"]
        if metadata.get("to_address"):
            message["To"] = metadata["to_address"]
        message.set_content(body)
        output_path.write_text(message.as_string())

    def _write_docx(self, rendered_text: str, output_path: Path, heading: str | None = None) -> None:
        paragraphs: List[str] = []
        if heading:
            paragraphs.append(str(heading))
        paragraphs.extend([block.strip() for block in rendered_text.split("\n\n") if block.strip()])
        document_xml = self._build_document_xml(paragraphs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output_path, "w") as archive:
            archive.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
            archive.writestr("_rels/.rels", RELS_XML)
            archive.writestr("word/_rels/document.xml.rels", DOC_RELS_XML)
            archive.writestr("word/document.xml", document_xml)

    def _build_document_xml(self, paragraphs: List[str]) -> str:
        paragraph_xml = "".join(self._paragraph_xml(text) for text in paragraphs)
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14">
  <w:body>
    {paragraph_xml}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    def _paragraph_xml(self, text: str) -> str:
        escaped = xml_utils.escape(text)
        return f"<w:p><w:r><w:t xml:space=\"preserve\">{escaped}</w:t></w:r></w:p>"
