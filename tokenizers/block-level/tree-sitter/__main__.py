"""
Initialize tree-sitter
"""
import os

from tree_sitter import Language


def main() -> None:
    """
    Initialize tree-sitter library.

    :return: None
    """
    # root directory for tree-sitter
    tree_sitter_dir = os.path.abspath(os.path.dirname(__file__))
    # grammar locations
    c_grammar_loc = os.path.join(tree_sitter_dir, "tree-sitter-c")
    c_sharp_grammar_loc = os.path.join(tree_sitter_dir, "tree-sitter-c-sharp")
    cpp_grammar_loc = os.path.join(tree_sitter_dir, "tree-sitter-cpp")
    java_grammar_loc = os.path.join(tree_sitter_dir, "tree-sitter-java")
    # location for library
    bin_loc = os.path.join(tree_sitter_dir, "build/langs.so")
    # build everything
    Language.build_library(
        # Store the library in the `bin_loc`
        bin_loc,
        # Include languages
        [
            c_grammar_loc,
            c_sharp_grammar_loc,
            cpp_grammar_loc,
            java_grammar_loc
        ]
    )


if __name__ == "__main__":
    main()
