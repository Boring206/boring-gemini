
import pytest

from boring.rag.parser import TreeSitterParser


@pytest.fixture
def parser():
    p = TreeSitterParser()
    if not p.is_available():
        pytest.skip("tree-sitter-languages not installed")
    return p

def test_go_receiver_extraction(parser):
    code = """
package main

type Service struct{}

func (s *Service) ProcessData(id int) error {
    return nil
}

func RegularFunc() {}
"""
    chunks = parser.extract_chunks(code, "go")

    # Find the method
    method = next((c for c in chunks if c.type == "method"), None)
    assert method is not None
    assert method.name == "ProcessData"
    assert method.receiver == "Service"
    assert "func (s *Service) ProcessData" in method.signature

def test_typescript_interface_and_type(parser):
    code = """
interface User {
    id: string;
    name: string;
}

type ID = string | number;

class Account {
    getBalance(): number { return 0; }
}
"""
    chunks = parser.extract_chunks(code, "typescript")

    interface = next((c for c in chunks if c.type == "interface"), None)
    assert interface is not None
    assert interface.name == "User"

    type_alias = next((c for c in chunks if c.type == "type_alias"), None)
    assert type_alias is not None
    assert type_alias.name == "ID"

def test_javascript_react_component(parser):
    code = """
const MyComponent = ({ title }) => {
    return <div>{title}</div>;
};

export default function App() {
    return <MyComponent title="Hello" />;
}
"""
    chunks = parser.extract_chunks(code, "javascript")

    # Arrow function component
    comp = next((c for c in chunks if c.name == "MyComponent"), None)
    assert comp is not None
    assert comp.type == "function"

    app = next((c for c in chunks if c.name == "App"), None)
    assert app is not None

def test_cpp_namespace_and_template(parser):
    code = """
namespace core {
    template <typename T>
    class Buffer {
        T data;
    };

    void Init() {}
}
"""
    chunks = parser.extract_chunks(code, "cpp")

    ns = next((c for c in chunks if c.type == "namespace"), None)
    assert ns is not None
    assert ns.name == "core"

    cls = next((c for c in chunks if c.type == "class"), None)
    assert cls is not None
    assert cls.name == "Buffer"
