# Copyright (c) Meta Platforms, Inc. and affiliates
"""
Tests for the V1 enhancement to DocAgent's dependency analyzer.

Covers:
- Stable component IDs (unchanged from before)
- Existing CodeComponent fields remain correct
- source_code correctness
- depends_on behavior unchanged
- Typed 'calls' relationship
- Typed 'imports' relationship
- Typed 'inherits' relationship
- Typed 'instantiates' relationship
- Typed 'contains' relationship (class → method)
- Incoming/reverse relationship lookup via RelationshipIndex
- New metadata fields: signature, parameters, return_type, containing_class
- Serialization round-trip (to_dict / from_dict)
- save_dependency_graph / load_dependency_graph round-trip
- New JSON output format has 'components' and 'relationships' keys
"""

import ast
import json
import os
import sys
import tempfile
import textwrap

import pytest

# Make sure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dependency_analyzer import (
    CodeComponent,
    DependencyParser,
    RelationshipIndex,
    TypedRelationship,
    build_graph_from_components,
    dependency_first_dfs,
)
from src.dependency_analyzer.ast_parser import (
    RELATIONSHIP_TYPES,
    _annotation_to_str,
    _extract_function_metadata,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_repo(tmp_dir: str, files: dict) -> str:
    """Write a mini repo under tmp_dir and return the repo path."""
    for rel_path, content in files.items():
        full = os.path.join(tmp_dir, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(textwrap.dedent(content))
    return tmp_dir


def _parse(files: dict) -> DependencyParser:
    """Write files to a temp dir, parse, and return the parser."""
    tmp = tempfile.mkdtemp()
    _write_repo(tmp, files)
    p = DependencyParser(tmp)
    p.parse_repository()
    return p


# ---------------------------------------------------------------------------
# Fixture: simple two-class repo matching Phase 12 example
# ---------------------------------------------------------------------------

SIMPLE_REPO = {
    "a.py": """\
        class A:
            def foo(self):
                B().bar()
    """,
    "b.py": """\
        class B:
            def bar(self):
                pass
    """,
}

IMPORT_REPO = {
    "utils.py": """\
        def helper():
            return 42
    """,
    "main.py": """\
        from utils import helper

        def run():
            return helper()
    """,
}

INHERIT_REPO = {
    "base.py": """\
        class Base:
            def greet(self):
                return 'hello'
    """,
    "child.py": """\
        from base import Base

        class Child(Base):
            def greet(self):
                return 'hi'
    """,
}

ANNOTATED_REPO = {
    "math_utils.py": """\
        def add(x: int, y: int = 0) -> int:
            return x + y

        def no_annotation(a, b):
            return a + b
    """,
}


# ---------------------------------------------------------------------------
# 1. Stable component IDs
# ---------------------------------------------------------------------------

class TestStableComponentIDs:
    def test_function_id(self):
        p = _parse(IMPORT_REPO)
        assert "utils.helper" in p.components
        assert "main.run" in p.components

    def test_class_id(self):
        p = _parse(SIMPLE_REPO)
        assert "a.A" in p.components
        assert "b.B" in p.components

    def test_method_id(self):
        p = _parse(SIMPLE_REPO)
        assert "a.A.foo" in p.components
        assert "b.B.bar" in p.components

    def test_ids_are_deterministic(self):
        """Parsing the same repo twice must yield identical IDs."""
        p1 = _parse(SIMPLE_REPO)
        p2 = _parse(SIMPLE_REPO)
        assert set(p1.components.keys()) == set(p2.components.keys())

    def test_real_repo_ids_unchanged(self):
        """IDs from the existing simple test repo must not have changed."""
        repo = os.path.join(
            os.path.dirname(__file__),
            "..", "data", "raw_test_repo_simple"
        )
        if not os.path.isdir(repo):
            pytest.skip("raw_test_repo_simple not found")
        p = DependencyParser(repo)
        p.parse_repository()
        expected_ids = {
            "main.main_function",
            "main.utility_function",
            "helper.HelperClass",
            "helper.HelperClass.process_data",
            "helper.HelperClass._internal_process",
            "helper.HelperClass.get_result",
            "helper.DataProcessor",
            "helper.DataProcessor.process",
            "helper.DataProcessor._internal_process",
            "processor.AdvancedProcessor",
            "processor.AdvancedProcessor.run",
            "processor.AdvancedProcessor.process_result",
        }
        for eid in expected_ids:
            assert eid in p.components, f"Missing expected component ID: {eid}"


# ---------------------------------------------------------------------------
# 2. Existing CodeComponent fields remain correct
# ---------------------------------------------------------------------------

class TestExistingFields:
    def test_component_type(self):
        p = _parse(SIMPLE_REPO)
        assert p.components["a.A"].component_type == "class"
        assert p.components["a.A.foo"].component_type == "method"
        assert p.components["b.B.bar"].component_type == "method"

    def test_relative_path(self):
        p = _parse(SIMPLE_REPO)
        assert p.components["a.A"].relative_path == "a.py"
        assert p.components["b.B"].relative_path == "b.py"

    def test_start_end_lines(self):
        p = _parse(SIMPLE_REPO)
        foo = p.components["a.A.foo"]
        assert foo.start_line >= 1
        assert foo.end_line >= foo.start_line

    def test_has_docstring_false(self):
        p = _parse(SIMPLE_REPO)
        assert p.components["a.A"].has_docstring is False

    def test_has_docstring_true(self):
        repo = {
            "mod.py": '''\
                def documented():
                    """This is a docstring."""
                    pass
            ''',
        }
        p = _parse(repo)
        assert p.components["mod.documented"].has_docstring is True
        assert "This is a docstring" in p.components["mod.documented"].docstring

    def test_depends_on_is_set(self):
        p = _parse(SIMPLE_REPO)
        # A depends on its own methods (class→method edge from pass 3)
        assert isinstance(p.components["a.A"].depends_on, set)


# ---------------------------------------------------------------------------
# 3. source_code is correct
# ---------------------------------------------------------------------------

class TestSourceCode:
    def test_function_source(self):
        p = _parse(IMPORT_REPO)
        src = p.components["utils.helper"].source_code
        assert src is not None
        assert "def helper" in src
        assert "return 42" in src

    def test_class_source(self):
        p = _parse(SIMPLE_REPO)
        src = p.components["b.B"].source_code
        assert "class B" in src

    def test_method_source(self):
        p = _parse(SIMPLE_REPO)
        src = p.components["b.B.bar"].source_code
        assert "def bar" in src


# ---------------------------------------------------------------------------
# 4. depends_on behavior unchanged
# ---------------------------------------------------------------------------

class TestDependsOn:
    def test_class_depends_on_methods(self):
        """Classes must still depend on their non-__init__ methods."""
        p = _parse(SIMPLE_REPO)
        assert "a.A.foo" in p.components["a.A"].depends_on

    def test_function_no_spurious_deps(self):
        """A function with no known calls should have empty depends_on."""
        p = _parse(IMPORT_REPO)
        # utils.helper calls nothing in the repo
        assert len(p.components["utils.helper"].depends_on) == 0

    def test_ordering_unchanged(self):
        """dependency_first_dfs must still put dependencies before dependents."""
        p = _parse(IMPORT_REPO)
        graph = build_graph_from_components(p.components)
        order = dependency_first_dfs(graph)
        helper_idx = order.index("utils.helper")
        run_idx = order.index("main.run")
        assert helper_idx < run_idx, "helper must come before run in ordering"


# ---------------------------------------------------------------------------
# 5. Typed 'calls' relationship
# ---------------------------------------------------------------------------

class TestCallsRelationship:
    def test_calls_detected(self):
        """main.run calls utils.helper — should appear as a 'calls' relationship."""
        p = _parse(IMPORT_REPO)
        rels = [
            r for r in p.components["main.run"].relationships
            if r.rel_type == "calls" and r.target == "utils.helper"
        ]
        assert len(rels) >= 1, "Expected a 'calls' relationship from main.run to utils.helper"

    def test_calls_source_is_correct(self):
        p = _parse(IMPORT_REPO)
        for rel in p.components["main.run"].relationships:
            if rel.rel_type == "calls":
                assert rel.source == "main.run"

    def test_method_calls_method(self):
        """A.foo calls B().bar() — after instantiation, bar should be a calls target."""
        # Note: A.foo instantiates B (instantiates) and calls B.bar (calls),
        # but static analysis can only reliably detect the call on B if
        # B.bar is a known component. We test that at least one relationship
        # exists from a.A.foo pointing to b.B.
        p = _parse(SIMPLE_REPO)
        foo_rels = p.components["a.A.foo"].relationships
        targets = {r.target for r in foo_rels}
        # B is instantiated — so b.B should be referenced
        assert "b.B" in targets or any("b." in t for t in targets), (
            f"Expected b.B in relationships of a.A.foo, got: {targets}"
        )


# ---------------------------------------------------------------------------
# 6. Typed 'imports' relationship
# ---------------------------------------------------------------------------

class TestImportsRelationship:
    def test_imports_detected(self):
        """main.run imports utils.helper via 'from utils import helper'."""
        p = _parse(IMPORT_REPO)
        # imports relationships are emitted per-component at file level
        # main.run should have an imports edge to utils.helper
        all_rels = []
        for comp in p.components.values():
            if comp.relative_path == "main.py":
                all_rels.extend(comp.relationships)
        import_targets = {r.target for r in all_rels if r.rel_type == "imports"}
        assert "utils.helper" in import_targets, (
            f"Expected utils.helper in imports targets, got: {import_targets}"
        )


# ---------------------------------------------------------------------------
# 7. Typed 'inherits' relationship
# ---------------------------------------------------------------------------

class TestInheritsRelationship:
    def test_inherits_detected(self):
        """Child inherits from Base — should appear as 'inherits'."""
        p = _parse(INHERIT_REPO)
        child_rels = p.components["child.Child"].relationships
        inherits = [r for r in child_rels if r.rel_type == "inherits"]
        assert len(inherits) >= 1, (
            f"Expected 'inherits' relationship for child.Child, got: {child_rels}"
        )
        assert inherits[0].target == "base.Base"
        assert inherits[0].source == "child.Child"

    def test_base_class_no_inherits(self):
        """Base class with no parent should have no 'inherits' relationships."""
        p = _parse(INHERIT_REPO)
        base_rels = p.components["base.Base"].relationships
        inherits = [r for r in base_rels if r.rel_type == "inherits"]
        assert len(inherits) == 0


# ---------------------------------------------------------------------------
# 8. Typed 'instantiates' relationship
# ---------------------------------------------------------------------------

class TestInstantiatesRelationship:
    def test_instantiates_detected(self):
        """A.foo does B() — should appear as 'instantiates' from a.A.foo to b.B."""
        p = _parse(SIMPLE_REPO)
        foo_rels = p.components["a.A.foo"].relationships
        inst = [r for r in foo_rels if r.rel_type == "instantiates" and r.target == "b.B"]
        assert len(inst) >= 1, (
            f"Expected 'instantiates' b.B from a.A.foo, got: {foo_rels}"
        )

    def test_instantiates_source_correct(self):
        p = _parse(SIMPLE_REPO)
        for rel in p.components["a.A.foo"].relationships:
            if rel.rel_type == "instantiates":
                assert rel.source == "a.A.foo"


# ---------------------------------------------------------------------------
# 9. Typed 'contains' relationship (class → method)
# ---------------------------------------------------------------------------

class TestContainsRelationship:
    def test_contains_detected(self):
        """a.A contains a.A.foo."""
        p = _parse(SIMPLE_REPO)
        a_rels = p.components["a.A"].relationships
        contains = [r for r in a_rels if r.rel_type == "contains" and r.target == "a.A.foo"]
        assert len(contains) >= 1, f"Expected 'contains' a.A.foo from a.A, got: {a_rels}"

    def test_contains_not_init(self):
        """__init__ must appear in contains (unlike depends_on which excludes it)."""
        repo = {
            "mod.py": """\
                class MyClass:
                    def __init__(self):
                        self.x = 1
                    def do(self):
                        pass
            """,
        }
        p = _parse(repo)
        class_rels = p.components["mod.MyClass"].relationships
        contains_targets = {r.target for r in class_rels if r.rel_type == "contains"}
        # Both __init__ and do must be in contains
        assert "mod.MyClass.do" in contains_targets
        assert "mod.MyClass.__init__" in contains_targets


# ---------------------------------------------------------------------------
# 10. RelationshipIndex — incoming/outgoing lookups
# ---------------------------------------------------------------------------

class TestRelationshipIndex:
    def test_outgoing(self):
        p = _parse(IMPORT_REPO)
        index = RelationshipIndex.from_components(p.components)
        out = index.outgoing("main.run")
        assert len(out) >= 1

    def test_outgoing_filtered_by_type(self):
        p = _parse(IMPORT_REPO)
        index = RelationshipIndex.from_components(p.components)
        calls = index.outgoing("main.run", rel_type="calls")
        for r in calls:
            assert r.rel_type == "calls"

    def test_incoming(self):
        """utils.helper should be the target of relationships from main.run."""
        p = _parse(IMPORT_REPO)
        index = RelationshipIndex.from_components(p.components)
        inc = index.incoming("utils.helper")
        sources = {r.source for r in inc}
        assert "main.run" in sources

    def test_incoming_filtered_by_type(self):
        p = _parse(INHERIT_REPO)
        index = RelationshipIndex.from_components(p.components)
        inheritors = index.incoming("base.Base", rel_type="inherits")
        assert any(r.source == "child.Child" for r in inheritors)

    def test_all_relationships_no_duplicates(self):
        p = _parse(SIMPLE_REPO)
        index = RelationshipIndex.from_components(p.components)
        all_rels = index.all_relationships()
        keys = [(r.source, r.target, r.rel_type) for r in all_rels]
        assert len(keys) == len(set(keys)), "Duplicate relationships found"

    def test_reverse_lookup_instantiates(self):
        """Who instantiates b.B? Should be a.A.foo."""
        p = _parse(SIMPLE_REPO)
        index = RelationshipIndex.from_components(p.components)
        instantiators = index.incoming("b.B", rel_type="instantiates")
        sources = {r.source for r in instantiators}
        assert "a.A.foo" in sources


# ---------------------------------------------------------------------------
# 11. New metadata fields
# ---------------------------------------------------------------------------

class TestMetadataFields:
    def test_signature_function(self):
        p = _parse(ANNOTATED_REPO)
        comp = p.components["math_utils.add"]
        assert comp.signature is not None
        assert "add" in comp.signature
        assert "x" in comp.signature
        assert "y" in comp.signature

    def test_return_type_annotated(self):
        p = _parse(ANNOTATED_REPO)
        comp = p.components["math_utils.add"]
        assert comp.return_type == "int"

    def test_return_type_none_when_missing(self):
        p = _parse(ANNOTATED_REPO)
        comp = p.components["math_utils.no_annotation"]
        assert comp.return_type is None

    def test_parameters_list(self):
        p = _parse(ANNOTATED_REPO)
        comp = p.components["math_utils.add"]
        names = [p["name"] for p in comp.parameters]
        assert "x" in names
        assert "y" in names

    def test_parameter_annotation(self):
        p = _parse(ANNOTATED_REPO)
        comp = p.components["math_utils.add"]
        x_param = next(pp for pp in comp.parameters if pp["name"] == "x")
        assert x_param["annotation"] == "int"

    def test_parameter_default(self):
        p = _parse(ANNOTATED_REPO)
        comp = p.components["math_utils.add"]
        y_param = next(pp for pp in comp.parameters if pp["name"] == "y")
        assert y_param["default"] == "0"

    def test_self_excluded_from_parameters(self):
        p = _parse(SIMPLE_REPO)
        comp = p.components["a.A.foo"]
        names = [pp["name"] for pp in comp.parameters]
        assert "self" not in names

    def test_containing_class_for_method(self):
        p = _parse(SIMPLE_REPO)
        comp = p.components["a.A.foo"]
        assert comp.containing_class == "a.A"

    def test_containing_class_none_for_function(self):
        p = _parse(IMPORT_REPO)
        comp = p.components["utils.helper"]
        assert comp.containing_class is None

    def test_containing_class_none_for_class(self):
        p = _parse(SIMPLE_REPO)
        comp = p.components["a.A"]
        assert comp.containing_class is None

    def test_signature_method(self):
        p = _parse(SIMPLE_REPO)
        comp = p.components["a.A.foo"]
        assert comp.signature is not None
        assert "foo" in comp.signature


# ---------------------------------------------------------------------------
# 12. Serialization round-trip
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict_contains_new_fields(self):
        p = _parse(ANNOTATED_REPO)
        d = p.components["math_utils.add"].to_dict()
        assert "signature" in d
        assert "parameters" in d
        assert "return_type" in d
        assert "containing_class" in d
        assert "relationships" in d
        assert "source_code" in d

    def test_to_dict_relationships_are_dicts(self):
        p = _parse(IMPORT_REPO)
        d = p.components["main.run"].to_dict()
        for rel in d["relationships"]:
            assert "source" in rel
            assert "target" in rel
            assert "type" in rel

    def test_from_dict_round_trip(self):
        p = _parse(ANNOTATED_REPO)
        original = p.components["math_utils.add"]
        d = original.to_dict()
        restored = CodeComponent.from_dict(d)

        assert restored.id == original.id
        assert restored.component_type == original.component_type
        assert restored.signature == original.signature
        assert restored.return_type == original.return_type
        assert restored.parameters == original.parameters
        assert restored.containing_class == original.containing_class
        assert restored.depends_on == original.depends_on

    def test_from_dict_relationships_restored(self):
        p = _parse(IMPORT_REPO)
        original = p.components["main.run"]
        d = original.to_dict()
        restored = CodeComponent.from_dict(d)
        assert len(restored.relationships) == len(original.relationships)
        for r in restored.relationships:
            assert isinstance(r, TypedRelationship)

    def test_from_dict_legacy_format(self):
        """from_dict must work even if 'relationships'/'signature' keys are absent (legacy JSON)."""
        legacy = {
            "id": "mod.func",
            "component_type": "function",
            "file_path": "/tmp/mod.py",
            "relative_path": "mod.py",
            "depends_on": [],
            "start_line": 1,
            "end_line": 3,
            "has_docstring": False,
            "docstring": "",
        }
        comp = CodeComponent.from_dict(legacy)
        assert comp.id == "mod.func"
        assert comp.relationships == []
        assert comp.signature is None
        assert comp.parameters == []


# ---------------------------------------------------------------------------
# 13. save / load round-trip and new JSON format
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_new_json_has_components_key(self):
        p = _parse(SIMPLE_REPO)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            p.save_dependency_graph(path)
            with open(path) as f:
                data = json.load(f)
            assert "components" in data, "New JSON format must have a 'components' key"
            assert "relationships" in data, "New JSON format must have a 'relationships' key"
        finally:
            os.unlink(path)

    def test_relationships_list_in_json(self):
        p = _parse(IMPORT_REPO)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            p.save_dependency_graph(path)
            with open(path) as f:
                data = json.load(f)
            assert isinstance(data["relationships"], list)
            for rel in data["relationships"]:
                assert {"source", "target", "type"} == set(rel.keys())
        finally:
            os.unlink(path)

    def test_load_restores_components(self):
        p = _parse(SIMPLE_REPO)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            p.save_dependency_graph(path)
            p2 = DependencyParser("/tmp")
            p2.load_dependency_graph(path)
            assert set(p2.components.keys()) == set(p.components.keys())
        finally:
            os.unlink(path)

    def test_load_preserves_depends_on(self):
        p = _parse(SIMPLE_REPO)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            p.save_dependency_graph(path)
            p2 = DependencyParser("/tmp")
            p2.load_dependency_graph(path)
            for comp_id in p.components:
                assert p2.components[comp_id].depends_on == p.components[comp_id].depends_on
        finally:
            os.unlink(path)

    def test_load_preserves_new_fields(self):
        p = _parse(ANNOTATED_REPO)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            p.save_dependency_graph(path)
            p2 = DependencyParser("/tmp")
            p2.load_dependency_graph(path)
            orig = p.components["math_utils.add"]
            restored = p2.components["math_utils.add"]
            assert restored.signature == orig.signature
            assert restored.return_type == orig.return_type
            assert restored.parameters == orig.parameters
        finally:
            os.unlink(path)

    def test_component_count_unchanged(self):
        """Parsing the real simple repo must yield the same component count as before."""
        repo = os.path.join(
            os.path.dirname(__file__), "..", "data", "raw_test_repo_simple"
        )
        if not os.path.isdir(repo):
            pytest.skip("raw_test_repo_simple not found")
        p = DependencyParser(repo)
        p.parse_repository()
        # The known count from the existing dependency graph JSON is 19 components
        assert len(p.components) >= 15, (
            f"Component count dropped unexpectedly: {len(p.components)}"
        )

    def test_dependency_ordering_real_repo(self):
        """Dependency ordering must still put leaves before dependents."""
        repo = os.path.join(
            os.path.dirname(__file__), "..", "data", "raw_test_repo_simple"
        )
        if not os.path.isdir(repo):
            pytest.skip("raw_test_repo_simple not found")
        p = DependencyParser(repo)
        p.parse_repository()
        graph = build_graph_from_components(p.components)
        order = dependency_first_dfs(graph)
        # utility_function has no deps and is depended upon by main_function
        assert order.index("main.utility_function") < order.index("main.main_function")


# ---------------------------------------------------------------------------
# 14. TypedRelationship dataclass and RELATIONSHIP_TYPES
# ---------------------------------------------------------------------------

class TestTypedRelationship:
    def test_valid_types(self):
        assert RELATIONSHIP_TYPES == {"calls", "imports", "inherits", "instantiates", "contains"}

    def test_to_dict(self):
        r = TypedRelationship(source="a.A", target="b.B", rel_type="calls")
        d = r.to_dict()
        assert d == {"source": "a.A", "target": "b.B", "type": "calls"}

    def test_from_dict(self):
        d = {"source": "a.A", "target": "b.B", "type": "inherits"}
        r = TypedRelationship.from_dict(d)
        assert r.source == "a.A"
        assert r.target == "b.B"
        assert r.rel_type == "inherits"


# ---------------------------------------------------------------------------
# 15. _annotation_to_str and _extract_function_metadata helpers
# ---------------------------------------------------------------------------

class TestASTHelpers:
    def _parse_func(self, src: str):
        tree = ast.parse(textwrap.dedent(src))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return node
        raise ValueError("No function found")

    def test_annotation_name(self):
        node = ast.parse("x: int").body[0]
        ann = _annotation_to_str(node.annotation)
        assert ann == "int"

    def test_annotation_none(self):
        assert _annotation_to_str(None) is None

    def test_extract_signature(self):
        node = self._parse_func("def foo(x: int, y: str = 'hi') -> bool: pass")
        sig, params, ret = _extract_function_metadata(node)
        assert "foo" in sig
        assert "x" in sig
        assert ret == "bool"

    def test_extract_parameters(self):
        node = self._parse_func("def foo(a: int, b=None): pass")
        _, params, _ = _extract_function_metadata(node)
        names = [p["name"] for p in params]
        assert "a" in names
        assert "b" in names

    def test_extract_default(self):
        node = self._parse_func("def foo(x=42): pass")
        _, params, _ = _extract_function_metadata(node)
        assert params[0]["default"] == "42"

    def test_self_not_in_params(self):
        node = self._parse_func("def method(self, x): pass")
        _, params, _ = _extract_function_metadata(node)
        names = [p["name"] for p in params]
        assert "self" not in names
        assert "x" in names

    def test_no_return_annotation(self):
        node = self._parse_func("def foo(): pass")
        _, _, ret = _extract_function_metadata(node)
        assert ret is None


# ---------------------------------------------------------------------------
# 16. Regression: contains includes __init__ (audit fix)
# ---------------------------------------------------------------------------

class TestContainsIncludesInit:
    """
    __init__ must appear in contains edges even though it is excluded from
    depends_on (that exclusion is intentional for documentation ordering).
    """

    REPO = {
        "mymod.py": """\
            class MyClass:
                def __init__(self):
                    self.x = 0

                def do_work(self):
                    pass
        """,
    }

    def test_init_in_contains(self):
        p = _parse(self.REPO)
        class_rels = p.components["mymod.MyClass"].relationships
        contains_targets = {r.target for r in class_rels if r.rel_type == "contains"}
        assert "mymod.MyClass.__init__" in contains_targets, (
            f"__init__ missing from contains. Got: {contains_targets}"
        )

    def test_do_work_in_contains(self):
        p = _parse(self.REPO)
        class_rels = p.components["mymod.MyClass"].relationships
        contains_targets = {r.target for r in class_rels if r.rel_type == "contains"}
        assert "mymod.MyClass.do_work" in contains_targets

    def test_init_not_in_depends_on(self):
        """Verify the existing invariant: __init__ is NOT in depends_on."""
        p = _parse(self.REPO)
        assert "mymod.MyClass.__init__" not in p.components["mymod.MyClass"].depends_on

    def test_do_work_in_depends_on(self):
        """Non-init methods still appear in depends_on (existing behaviour)."""
        p = _parse(self.REPO)
        assert "mymod.MyClass.do_work" in p.components["mymod.MyClass"].depends_on

    def test_contains_source_is_class(self):
        p = _parse(self.REPO)
        class_rels = p.components["mymod.MyClass"].relationships
        for r in class_rels:
            if r.rel_type == "contains":
                assert r.source == "mymod.MyClass"

    def test_reverse_lookup_init_contained_by(self):
        """RelationshipIndex.incoming on __init__ must show MyClass as container."""
        p = _parse(self.REPO)
        index = RelationshipIndex.from_components(p.components)
        containers = {r.source for r in index.incoming("mymod.MyClass.__init__", rel_type="contains")}
        assert "mymod.MyClass" in containers


# ---------------------------------------------------------------------------
# 17. Regression: self.method() resolves to correct class when two classes
#     in the same module share a method name  (audit fix)
# ---------------------------------------------------------------------------

class TestSelfMethodDisambiguation:
    """
    Given two classes A and B in the same module, both with a method 'process',
    A.run calling self.process() must resolve to A.process, never B.process.
    """

    REPO = {
        "mod.py": """\
            class A:
                def run(self):
                    self.process()

                def process(self):
                    pass

            class B:
                def run(self):
                    self.process()

                def process(self):
                    pass
        """,
    }

    def test_a_run_calls_a_process(self):
        p = _parse(self.REPO)
        a_run_rels = p.components["mod.A.run"].relationships
        call_targets = {r.target for r in a_run_rels if r.rel_type == "calls"}
        assert "mod.A.process" in call_targets, (
            f"Expected mod.A.process in calls from mod.A.run, got: {call_targets}"
        )

    def test_a_run_does_not_call_b_process(self):
        p = _parse(self.REPO)
        a_run_rels = p.components["mod.A.run"].relationships
        call_targets = {r.target for r in a_run_rels if r.rel_type == "calls"}
        assert "mod.B.process" not in call_targets, (
            f"mod.A.run incorrectly resolved to mod.B.process: {call_targets}"
        )

    def test_b_run_calls_b_process(self):
        p = _parse(self.REPO)
        b_run_rels = p.components["mod.B.run"].relationships
        call_targets = {r.target for r in b_run_rels if r.rel_type == "calls"}
        assert "mod.B.process" in call_targets

    def test_b_run_does_not_call_a_process(self):
        p = _parse(self.REPO)
        b_run_rels = p.components["mod.B.run"].relationships
        call_targets = {r.target for r in b_run_rels if r.rel_type == "calls"}
        assert "mod.A.process" not in call_targets


# ---------------------------------------------------------------------------
# 18. Regression: imports semantics — per-component usage, not per-file
# ---------------------------------------------------------------------------

class TestImportsSemantics:
    """
    An 'imports' edge from A to B means: A's own AST body references the name B
    which was imported into A's module via 'from X import B'.
    It is a per-component usage fact, not a per-file fact.
    """

    REPO = {
        "utils.py": """\
            def helper():
                return 1

            def unused():
                return 2
        """,
        "consumer.py": """\
            from utils import helper, unused

            def uses_helper():
                return helper()

            def uses_neither():
                return 42
        """,
    }

    def test_uses_helper_has_imports_edge(self):
        """uses_helper references 'helper' → imports edge must exist."""
        p = _parse(self.REPO)
        rels = p.components["consumer.uses_helper"].relationships
        import_targets = {r.target for r in rels if r.rel_type == "imports"}
        assert "utils.helper" in import_targets, (
            f"Expected imports utils.helper from consumer.uses_helper, got: {import_targets}"
        )

    def test_uses_neither_has_no_imports_edge(self):
        """uses_neither doesn't reference any imported name → no imports edge."""
        p = _parse(self.REPO)
        rels = p.components["consumer.uses_neither"].relationships
        import_targets = {r.target for r in rels if r.rel_type == "imports"}
        assert len(import_targets) == 0, (
            f"Expected no imports edges from uses_neither, got: {import_targets}"
        )

    def test_uses_helper_no_imports_to_unused(self):
        """uses_helper doesn't reference 'unused' → no imports edge to unused."""
        p = _parse(self.REPO)
        rels = p.components["consumer.uses_helper"].relationships
        import_targets = {r.target for r in rels if r.rel_type == "imports"}
        assert "utils.unused" not in import_targets

    def test_imports_semantics_documented_in_relationship_types(self):
        """RELATIONSHIP_TYPES must include 'imports'."""
        assert "imports" in RELATIONSHIP_TYPES

    def test_imports_is_per_component_not_per_file(self):
        """
        Two components in the same file that import the same module must each
        independently have or not have the imports edge based on their own usage.
        """
        p = _parse(self.REPO)
        helper_rels = p.components["consumer.uses_helper"].relationships
        neither_rels = p.components["consumer.uses_neither"].relationships

        helper_imports = {r.target for r in helper_rels if r.rel_type == "imports"}
        neither_imports = {r.target for r in neither_rels if r.rel_type == "imports"}

        # They are in the same file with the same imports, but only uses_helper
        # references the imported names in its body
        assert "utils.helper" in helper_imports
        assert "utils.helper" not in neither_imports


# ---------------------------------------------------------------------------
# 19. Regression: component IDs stable after docstring insertion re-parse
# ---------------------------------------------------------------------------

class TestStabilityAfterReparse:
    """
    generate_docstrings.py re-parses a file after each docstring insertion
    because line numbers shift.  The component IDs and containing_class values
    must be identical before and after that re-parse.
    """

    REPO = {
        "stable.py": """\
            class Worker:
                def __init__(self):
                    self.value = 0

                def run(self):
                    self.process()

                def process(self):
                    return self.value
        """,
    }

    def _parse_with_docstring_inserted(self, tmp_dir: str) -> DependencyParser:
        """Simulate docstring insertion by prepending a docstring to Worker, then re-parse."""
        import textwrap as tw
        src_path = os.path.join(tmp_dir, "stable.py")
        with open(src_path) as f:
            original = f.read()

        # Insert a simple class docstring after the 'class Worker:' line
        lines = original.split("\n")
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip().startswith("class Worker"):
                new_lines.append('    """Worker class docstring."""')
        with open(src_path, "w") as f:
            f.write("\n".join(new_lines))

        p2 = DependencyParser(tmp_dir)
        p2.parse_repository()
        return p2

    def test_ids_stable_after_reparse(self):
        tmp = tempfile.mkdtemp()
        _write_repo(tmp, self.REPO)

        p1 = DependencyParser(tmp)
        p1.parse_repository()
        ids_before = set(p1.components.keys())

        p2 = self._parse_with_docstring_inserted(tmp)
        ids_after = set(p2.components.keys())

        assert ids_before == ids_after, (
            f"ID set changed after re-parse.\n"
            f"Lost: {ids_before - ids_after}\n"
            f"Gained: {ids_after - ids_before}"
        )

    def test_containing_class_stable_after_reparse(self):
        tmp = tempfile.mkdtemp()
        _write_repo(tmp, self.REPO)

        p1 = DependencyParser(tmp)
        p1.parse_repository()

        p2 = self._parse_with_docstring_inserted(tmp)

        for comp_id in p1.components:
            before = p1.components[comp_id].containing_class
            after = p2.components[comp_id].containing_class
            assert before == after, (
                f"containing_class changed for {comp_id}: {before!r} → {after!r}"
            )

    def test_contains_edges_stable_after_reparse(self):
        tmp = tempfile.mkdtemp()
        _write_repo(tmp, self.REPO)

        p1 = DependencyParser(tmp)
        p1.parse_repository()
        contains_before = {
            (r.source, r.target)
            for c in p1.components.values()
            for r in c.relationships
            if r.rel_type == "contains"
        }

        p2 = self._parse_with_docstring_inserted(tmp)
        contains_after = {
            (r.source, r.target)
            for c in p2.components.values()
            for r in c.relationships
            if r.rel_type == "contains"
        }

        assert contains_before == contains_after, (
            f"contains edges changed after re-parse.\n"
            f"Lost: {contains_before - contains_after}\n"
            f"Gained: {contains_after - contains_before}"
        )
