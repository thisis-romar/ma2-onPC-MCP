# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the knowledge graph Python AST extractor."""

from __future__ import annotations

import textwrap

from src.knowledge_graph.parsers.extractor import (
    _path_to_module_name,
    extract_module_info,
)


class TestPathToModuleName:
    def test_simple_module(self):
        assert _path_to_module_name("src/server.py") == "src.server"

    def test_nested_module(self):
        assert _path_to_module_name("src/knowledge_graph/store.py") == "src.knowledge_graph.store"

    def test_init_file(self):
        assert _path_to_module_name("src/knowledge_graph/__init__.py") == "src.knowledge_graph"

    def test_top_level(self):
        assert _path_to_module_name("setup.py") == "setup"

    def test_backslash_path(self):
        assert _path_to_module_name("src\\server.py") == "src.server"

    def test_tests_dir(self):
        assert _path_to_module_name("tests/test_kg_store.py") == "tests.test_kg_store"


class TestExtractModuleInfoBasic:
    def test_simple_function(self):
        source = textwrap.dedent("""\
            def hello():
                pass
        """)
        info = extract_module_info(source, "example.py")
        assert info.module_name == "example"
        assert info.path == "example.py"
        assert info.parse_error is None
        assert len(info.symbols) == 1
        assert info.symbols[0].name == "hello"
        assert info.symbols[0].kind == "function"
        assert info.symbols[0].line == 1

    def test_multiple_functions_and_class(self):
        source = textwrap.dedent("""\
            def foo():
                pass

            def bar():
                pass

            class MyClass:
                pass
        """)
        info = extract_module_info(source, "src/multi.py")
        assert info.module_name == "src.multi"
        names = [s.name for s in info.symbols]
        assert "foo" in names
        assert "bar" in names
        assert "MyClass" in names

    def test_async_function(self):
        source = textwrap.dedent("""\
            async def fetch_data():
                pass
        """)
        info = extract_module_info(source, "async_mod.py")
        assert len(info.symbols) == 1
        assert info.symbols[0].name == "fetch_data"
        assert info.symbols[0].kind == "function"


class TestDecoratorExtraction:
    def test_simple_decorator(self):
        source = textwrap.dedent("""\
            @staticmethod
            def my_func():
                pass
        """)
        info = extract_module_info(source, "dec.py")
        assert info.symbols[0].decorators == ["staticmethod"]

    def test_dotted_decorator(self):
        source = textwrap.dedent("""\
            @app.route
            def handler():
                pass
        """)
        info = extract_module_info(source, "dec.py")
        assert info.symbols[0].decorators == ["app.route"]

    def test_call_decorator(self):
        source = textwrap.dedent("""\
            @app.route("/api")
            def handler():
                pass
        """)
        info = extract_module_info(source, "dec.py")
        assert info.symbols[0].decorators == ["app.route"]

    def test_multiple_decorators(self):
        source = textwrap.dedent("""\
            @require_scope
            @require_ma2_right
            def protected():
                pass
        """)
        info = extract_module_info(source, "dec.py")
        assert info.symbols[0].decorators == ["require_scope", "require_ma2_right"]


class TestImportExtraction:
    def test_import_statement(self):
        source = textwrap.dedent("""\
            import os
            import sys
        """)
        info = extract_module_info(source, "imp.py")
        assert len(info.imports) == 2
        modules = [i.module for i in info.imports]
        assert "os" in modules
        assert "sys" in modules
        assert all(not i.is_relative for i in info.imports)

    def test_from_import(self):
        source = textwrap.dedent("""\
            from os.path import join, exists
        """)
        info = extract_module_info(source, "imp.py")
        assert len(info.imports) == 1
        assert info.imports[0].module == "os.path"
        assert info.imports[0].names == ["join", "exists"]
        assert info.imports[0].is_relative is False

    def test_relative_import(self):
        source = textwrap.dedent("""\
            from .schema import NodeType
        """)
        info = extract_module_info(source, "src/knowledge_graph/store.py")
        assert len(info.imports) == 1
        assert info.imports[0].module == "schema"
        assert info.imports[0].names == ["NodeType"]
        assert info.imports[0].is_relative is True

    def test_import_line_numbers(self):
        source = textwrap.dedent("""\
            import os

            from sys import argv
        """)
        info = extract_module_info(source, "imp.py")
        assert info.imports[0].line == 1
        assert info.imports[1].line == 3


class TestSyntaxErrorHandling:
    def test_syntax_error_returns_module_info_with_error(self):
        source = "def broken(:\n    pass"
        info = extract_module_info(source, "broken.py")
        assert info.parse_error is not None
        assert info.module_name == "broken"
        assert info.path == "broken.py"
        assert info.symbols == []
        assert info.imports == []

    def test_empty_source(self):
        info = extract_module_info("", "empty.py")
        assert info.parse_error is None
        assert info.symbols == []
        assert info.imports == []


class TestClassMethodExtraction:
    def test_methods_extracted(self):
        source = textwrap.dedent("""\
            class MyStore:
                def get(self):
                    pass

                def put(self, value):
                    pass
        """)
        info = extract_module_info(source, "store.py")
        # Should have: MyStore (class), get (method), put (method)
        assert len(info.symbols) == 3
        class_sym = [s for s in info.symbols if s.kind == "class"]
        method_syms = [s for s in info.symbols if s.kind == "method"]
        assert len(class_sym) == 1
        assert class_sym[0].name == "MyStore"
        assert len(method_syms) == 2
        assert all(m.parent_class == "MyStore" for m in method_syms)
        method_names = [m.name for m in method_syms]
        assert "get" in method_names
        assert "put" in method_names

    def test_async_method(self):
        source = textwrap.dedent("""\
            class Handler:
                async def handle(self):
                    pass
        """)
        info = extract_module_info(source, "handler.py")
        methods = [s for s in info.symbols if s.kind == "method"]
        assert len(methods) == 1
        assert methods[0].name == "handle"
        assert methods[0].parent_class == "Handler"


class TestDocstringExtraction:
    def test_function_docstring(self):
        source = textwrap.dedent('''\
            def hello():
                """Say hello to the world."""
                pass
        ''')
        info = extract_module_info(source, "doc.py")
        assert info.symbols[0].docstring == "Say hello to the world."

    def test_long_docstring_truncated(self):
        long_doc = "A" * 300
        source = f'def hello():\n    """{long_doc}"""\n    pass\n'
        info = extract_module_info(source, "doc.py")
        assert info.symbols[0].docstring is not None
        assert len(info.symbols[0].docstring) == 200

    def test_no_docstring(self):
        source = textwrap.dedent("""\
            def hello():
                pass
        """)
        info = extract_module_info(source, "doc.py")
        assert info.symbols[0].docstring is None

    def test_class_docstring(self):
        source = textwrap.dedent('''\
            class MyClass:
                """A well-documented class."""
                pass
        ''')
        info = extract_module_info(source, "doc.py")
        class_sym = [s for s in info.symbols if s.kind == "class"][0]
        assert class_sym.docstring == "A well-documented class."
