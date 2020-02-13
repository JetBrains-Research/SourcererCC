"""
Functionality to extract functions and related metadata for Java.
"""
from typing import List, Tuple, Union

import tree_sitter
from .parsers.utils import get_parser


def get_func_args(func_node: tree_sitter.Node, content: Union[bytes, str]) -> Union[bytes, str]:
    """
    Extract arguments given function node and file content.

    :param func_node: function node.
    :param content: file content that was used for parsing.
    :return: bytes/str for function arguments.
    """
    for node in func_node.children:
        if node.type == "formal_parameters":
            return content[node.start_byte:node.end_byte]


def get_func_name(func_node: tree_sitter.Node, content: Union[bytes, str]) -> Union[bytes, str]:
    """
    Extract function name given function node and file content.

    :param func_node: function node.
    :param content: file content that was used for parsing.
    :return: bytes/str for function name.
    """
    assert func_node.type in ["constructor_declaration", "method_declaration"]
    for node in func_node.children:
        if node.type == "identifier":
            return content[node.start_byte:node.end_byte]


def get_package_name(root_node: tree_sitter.Node, content: Union[bytes, str]) -> Union[bytes, str]:
    """
    Extract package name given root node and file content.

    :param root_node: root node after parsing of content.
    :param content: file content that was used for parsing.
    :return: bytes/str for Java package declaration or "JHawkDefaultPackage" for missed one as default.
    """
    for ch in root_node.children:
        if ch.type == "package_declaration":
            for ch_ in ch.children:
                if ch_.type == "scoped_identifier":
                    return content[ch_.start_byte:ch_.end_byte]
    return "JHawkDefaultPackage"


def get_lines(node: tree_sitter.Node) -> Tuple[int, int]:
    """
    Extract start and end line.
    :param node: function node.
    :return: (start line, end line)
    """
    start_line = node.start_point[0]
    end_line = node.end_point[0]
    return start_line, end_line


def get_positional_bytes(node: tree_sitter.Node) -> Tuple[int, int]:
    """
    Extract start and end byte.
    :param node: function node.
    :return: (start line, end line)
    """
    start = node.start_byte
    end = node.end_byte
    return start, end


def get_function_meta(func_node: tree_sitter.Node, package_name: Union[bytes, str], content: Union[bytes, str]) -> str:
    """
    Extract function metadata - package, name, arguments.

    :param func_node: function node.
    :param package_name: package name.
    :param content: file content that was used for parsing.
    :return:
    """
    assert isinstance(package_name, (bytes, str))
    try:
        package_name = package_name.decode("utf-8")
    except AttributeError:
        pass
    return (package_name + "." +
            get_func_name(func_node, content).decode("utf-8") +
            get_func_args(func_node, content).decode("utf-8"))


def get_functions(content: Union[bytes, str]) -> Tuple[List[Tuple[int, int]], List[bytes], List[str]]:
    """
    Parse and extract function given content.
    :param content: java-file content.
    :return: 3 lists. First contains list of tuples with start and end line number.
             Second contains functions itself.
             Third contains function metadata (package, name, arguments).

    """
    assert isinstance(content, (bytes, str))
    try:
        content = content.encode()
    except AttributeError:
        pass
    tree = get_parser("java").parse(content)
    func_types = set(['constructor_declaration', 'method_declaration'])
    root = tree.root_node
    package = get_package_name(root, content)

    func_lines = []
    func_bodies = []
    func_meta = []

    def add_children_nodes(node):
        for child in node.children:
            if child.type in func_types:
                func_meta.append(get_function_meta(child, package))
                func_lines.append(get_lines(child))
                start, end = get_positional_bytes(child)
                func_bodies.append(content[start:end])
            if len(child.children) != 0:
                add_children_nodes(child)
    add_children_nodes(root)
    return func_lines, func_bodies, func_meta
