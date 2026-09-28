# Copyright (c) Meta Platforms, Inc. and affiliates
"""
AST-based Python code parser that extracts dependency information between code components.

This module identifies imports and references between Python code components (functions, classes, methods)
and builds a dependency graph for topological sorting.

V1 Enhancement: Also extracts typed relationships (calls, imports, inherits, instantiates, contains)
and enriched component metadata (signature, parameters, return_type, containing_class) to support
downstream Retrieval, Mapping, and Verification agents.
"""

import ast
import os
import json
import logging
import builtins
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Built-in Python types and modules that should be excluded from dependencies
BUILTIN_TYPES = {name for name in dir(builtins)}
STANDARD_MODULES = {
    'abc', 'argparse', 'array', 'asyncio', 'base64', 'collections', 'copy', 
    'csv', 'datetime', 'enum', 'functools', 'glob', 'io', 'itertools', 
    'json', 'logging', 'math', 'os', 'pathlib', 'random', 're', 'shutil', 
    'string', 'sys', 'time', 'typing', 'uuid', 'warnings', 'xml'
}
EXCLUDED_NAMES = {'self', 'cls'}

# ---------------------------------------------------------------------------
# Typed relationship representation
# ---------------------------------------------------------------------------

# Valid relationship types derived purely from static analysis:
#
#   calls        – A (function or method) directly calls B (function or method).
#                  B must be a known component in this repository.
#
#   imports      – A's AST body references a symbol that was imported into A's
#                  module via a 'from X import Y' statement, AND that symbol
#                  resolves to a known component B.
#                  This is a per-component usage fact, not a per-file fact:
#                  an imports edge from A to B means A's own code references
#                  the imported name B, not merely that A's file imports it.
#                  (alias imports and 'import X' bare-module imports are not
#                  resolved in V1 and produce no edge.)
#
#   inherits     – A (class) directly inherits from B (class).
#                  Only direct base-class relationships are recorded; transitive
#                  inheritance is not stored in V1.
#
#   instantiates – A (function or method) creates an instance of B (class)
#                  via a direct call B() where B is a known class component.
#
#   contains     – A (class) structurally contains B (method).
#                  Derived from the containing_class field set on every method
#                  during parsing.  Includes __init__, unlike depends_on which
#                  intentionally excludes __init__ for documentation-ordering
#                  purposes.
RELATIONSHIP_TYPES = frozenset({"calls", "imports", "inherits", "instantiates", "contains"})


@dataclass
class TypedRelationship:
    """
    Represents a directional, typed relationship between two code components.

    The canonical form is (source, target, type) where:
      - source is the component ID of the component initiating the relationship
      - target is the component ID of the component being referenced
      - rel_type is one of: calls, imports, inherits, instantiates, contains
    """
    source: str    # component ID of the originating component
    target: str    # component ID of the referenced component
    rel_type: str  # one of RELATIONSHIP_TYPES

    def to_dict(self) -> Dict[str, str]:
        """Serialize to a JSON-compatible dictionary."""
        return {"source": self.source, "target": self.target, "type": self.rel_type}

    @staticmethod
    def from_dict(data: Dict[str, str]) -> "TypedRelationship":
        """Deserialize from a dictionary."""
        return TypedRelationship(
            source=data["source"],
            target=data["target"],
            rel_type=data["type"],
        )

@dataclass
class CodeComponent:
    """
    Represents a single code component (function, class, or method) in a Python codebase.

    Stores the component's identifier, AST node, dependencies, and other metadata.

    V1 Enhancement fields (all optional, derived from the same AST traversal):
      - signature: text signature of a function/method, e.g. "process_data(self, x: int)"
      - parameters: list of parameter dicts with keys 'name', 'annotation', 'default'
      - return_type: return annotation text, or None
      - containing_class: component ID of the enclosing class (methods only)
      - relationships: typed relationships originating from this component
    """
    # Unique identifier for the component, format: module_path.ClassName.method_name
    id: str
    
    # AST node representing this component
    node: ast.AST
    
    # Type of component: 'class', 'function', or 'method'
    component_type: str
    
    # Full path to the file containing this component
    file_path: str
    
    # Relative path within the repo
    relative_path: str
    
    # Set of component IDs this component depends on (unchanged — used for ordering)
    depends_on: Set[str] = field(default_factory=set)
    
    # Original source code of the component
    source_code: Optional[str] = None
    
    # Line numbers in the file (1-indexed)
    start_line: int = 0
    end_line: int = 0
    
    # Whether the component already has a docstring
    has_docstring: bool = False
    
    # Content of the docstring if it exists, empty string otherwise
    docstring: str = ""

    # -----------------------------------------------------------------------
    # V1 Enhancement — new optional metadata fields
    # -----------------------------------------------------------------------

    # Text signature of the function/method node (None for classes)
    signature: Optional[str] = None

    # Ordered list of parameters; each entry is a dict:
    #   { "name": str, "annotation": str|None, "default": str|None }
    # Empty list for classes or functions with no parameters (other than self/cls).
    parameters: List[Dict[str, Any]] = field(default_factory=list)

    # Return annotation text (None when not annotated or when component is a class)
    return_type: Optional[str] = None

    # Component ID of the immediately enclosing class; None for top-level functions/classes
    containing_class: Optional[str] = None

    # Typed relationships originating from this component (populated after pass 2/3)
    relationships: List[TypedRelationship] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert this component to a dictionary representation for JSON serialization."""
        return {
            'id': self.id,
            'component_type': self.component_type,
            'file_path': self.file_path,
            'relative_path': self.relative_path,
            'depends_on': list(self.depends_on),
            'source_code': self.source_code,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'has_docstring': self.has_docstring,
            'docstring': self.docstring,
            # V1 enhancement fields
            'signature': self.signature,
            'parameters': self.parameters,
            'return_type': self.return_type,
            'containing_class': self.containing_class,
            'relationships': [r.to_dict() for r in self.relationships],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CodeComponent':
        """Create a CodeComponent from a dictionary representation."""
        component = CodeComponent(
            id=data['id'],
            node=None,  # AST node is not serialized
            component_type=data['component_type'],
            file_path=data['file_path'],
            relative_path=data['relative_path'],
            depends_on=set(data.get('depends_on', [])),
            source_code=data.get('source_code'),
            start_line=data.get('start_line', 0),
            end_line=data.get('end_line', 0),
            has_docstring=data.get('has_docstring', False),
            docstring=data.get('docstring', ""),
            # V1 enhancement fields
            signature=data.get('signature'),
            parameters=data.get('parameters', []),
            return_type=data.get('return_type'),
            containing_class=data.get('containing_class'),
            relationships=[
                TypedRelationship.from_dict(r)
                for r in data.get('relationships', [])
            ],
        )
        return component


class ImportCollector(ast.NodeVisitor):
    """Collects import statements from Python code."""
    
    def __init__(self):
        self.imports = set()
        self.from_imports = {}  # module -> [names]
        
    def visit_Import(self, node: ast.Import):
        """Process 'import x' statements."""
        for name in node.names:
            self.imports.add(name.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Process 'from x import y' statements."""
        if node.module is not None:
            module = node.module
            if module not in self.from_imports:
                self.from_imports[module] = []
            
            for name in node.names:
                if name.name != '*':
                    self.from_imports[module].append(name.name)
        
        self.generic_visit(node)


class MethodDependencyCollector(ast.NodeVisitor):
    """
    Special dependency collector for methods that also tracks 'self.XXX' references
    as potential dependencies.
    """
    
    def __init__(self, class_id: str, method_id: str, class_methods: Dict[str, str]):
        self.class_id = class_id
        self.method_id = method_id
        self.class_methods = class_methods  # method_name -> full_method_id
        self.self_attr_refs = set()  # Set of attributes accessed via self.XXX
        
    def visit_Attribute(self, node: ast.Attribute):
        """Process attribute access, specifically looking for self.XXX references."""
        if (isinstance(node.value, ast.Name) and 
            node.value.id == 'self' and 
            isinstance(node.ctx, ast.Load)):
            
            # Found a self.XXX reference
            attr_name = node.attr
            self.self_attr_refs.add(attr_name)
        
        self.generic_visit(node)
    
    def get_method_dependencies(self) -> Set[str]:
        """
        Get the set of methods that this method depends on based on self.XXX references.
        
        Returns:
            A set of method IDs that this method depends on
        """
        dependencies = set()
        
        # Check if any self.attr references match method names
        for attr in self.self_attr_refs:
            if attr in self.class_methods:
                # This is a reference to another method in the class
                dependencies.add(self.class_methods[attr])
        
        return dependencies


class DependencyCollector(ast.NodeVisitor):
    """
    Collects dependencies between code components by analyzing
    attribute access, function calls, and class references.
    """
    
    def __init__(self, imports, from_imports, current_module, repo_modules):
        self.imports = imports
        self.from_imports = from_imports
        self.current_module = current_module
        self.repo_modules = repo_modules
        self.dependencies = set()
        self._current_class = None
        # Track local variables defined in the current context
        self.local_variables = set()
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Process class definitions."""
        old_class = self._current_class
        self._current_class = node.name
        
        # Check for base classes dependencies
        for base in node.bases:
            if isinstance(base, ast.Name):
                # Simple name reference, could be an imported class
                self._add_dependency(base.id)
            elif isinstance(base, ast.Attribute):
                # Module.Class reference
                self._process_attribute(base)
        
        self.generic_visit(node)
        self._current_class = old_class
    
    def visit_Assign(self, node: ast.Assign):
        """Track local variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Add to local variables
                self.local_variables.add(target.id)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Process function calls."""
        if isinstance(node.func, ast.Name):
            # Direct function call
            self._add_dependency(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Method call or module.function call
            self._process_attribute(node.func)
        
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """Process name references."""
        if isinstance(node.ctx, ast.Load):
            self._add_dependency(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Process attribute access."""
        self._process_attribute(node)
        self.generic_visit(node)
    
    def _process_attribute(self, node: ast.Attribute):
        """Process an attribute node to extract potential dependencies."""
        parts = []
        current = node
        
        # Traverse the attribute chain (e.g., module.submodule.Class.method)
        while isinstance(current, ast.Attribute):
            parts.insert(0, current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.insert(0, current.id)
            
            # Skip if the first part is a local variable
            if parts[0] in self.local_variables:
                return
                
            # Skip if the first part is in our excluded names
            if parts[0] in EXCLUDED_NAMES:
                return
                
            # Check if the first part is an imported module
            if parts[0] in self.imports:
                module_path = parts[0]
                # Skip standard library modules
                if module_path in STANDARD_MODULES:
                    return
                    
                # If it's a repo module, add as dependency
                if module_path in self.repo_modules:
                    if len(parts) > 1:
                        # Example: module.Class or module.function
                        self.dependencies.add(f"{module_path}.{parts[1]}")
            
            # Check from imports
            elif parts[0] in self.from_imports.keys():
                # Skip standard library modules
                if parts[0] in STANDARD_MODULES:
                    return
                    
                # Check if the name is in the imported names
                if len(parts) > 1 and parts[1] in self.from_imports[parts[0]]:
                    self.dependencies.add(f"{parts[0]}.{parts[1]}")
    
    def _add_dependency(self, name):
        """Add a potential dependency based on a name reference."""
        # Skip built-in types
        if name in BUILTIN_TYPES:
            return
            
        # Skip excluded names
        if name in EXCLUDED_NAMES:
            return
            
        # Skip local variables
        if name in self.local_variables:
            return
            
        # Check if name is directly imported from a module
        for module, imported_names in self.from_imports.items():
            # Skip standard library modules
            if module in STANDARD_MODULES:
                continue
                
            if name in imported_names and module in self.repo_modules:
                self.dependencies.add(f"{module}.{name}")
                return
                
        # Check if name refers to a component in the current module
        local_component_id = f"{self.current_module}.{name}"
        self.dependencies.add(local_component_id)


def add_parent_to_nodes(tree: ast.AST) -> None:
    """
    Add a 'parent' attribute to each node in the AST.
    
    Args:
        tree: The AST to process
    """
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node


# ---------------------------------------------------------------------------
# V1 Enhancement — AST-based metadata helpers
# ---------------------------------------------------------------------------

def _annotation_to_str(node: Optional[ast.expr]) -> Optional[str]:
    """
    Convert an AST annotation node to a human-readable string.

    Uses ast.unparse when available (Python ≥ 3.9); falls back to a best-effort
    walk for older versions.

    Args:
        node: An ast.expr annotation node, or None.

    Returns:
        A string representation of the annotation, or None if node is None.
    """
    if node is None:
        return None
    try:
        if hasattr(ast, "unparse"):
            return ast.unparse(node)
        # Fallback: handle the most common annotation shapes
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            cur = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            return ".".join(reversed(parts))
        if isinstance(node, ast.Subscript):
            val = _annotation_to_str(node.value)
            slc = _annotation_to_str(node.slice)
            return f"{val}[{slc}]"
        if isinstance(node, ast.Constant):
            return repr(node.value)
        # Unknown: return empty string rather than crash
        return ""
    except Exception:
        return None


def _extract_function_metadata(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
    """
    Extract signature text, parameter list, and return annotation from a function node.

    The 'self' and 'cls' parameters are included in the signature string but
    excluded from the returned parameters list (they carry no useful information
    for downstream consumers).

    Args:
        node: An ast.FunctionDef or ast.AsyncFunctionDef node.

    Returns:
        A 3-tuple: (signature_str, parameters_list, return_type_str)
        where parameters_list entries are:
            {"name": str, "annotation": str|None, "default": str|None}
    """
    args = node.args

    # Build default mapping: defaults align to the LAST n positional args
    all_args = args.args + args.posonlyargs
    n_defaults = len(args.defaults)
    # Position of the first argument that has a default
    default_start = len(all_args) - n_defaults
    default_map: Dict[str, Optional[str]] = {}
    for idx, arg in enumerate(all_args):
        if idx >= default_start:
            default_node = args.defaults[idx - default_start]
            try:
                default_map[arg.arg] = ast.unparse(default_node) if hasattr(ast, "unparse") else None
            except Exception:
                default_map[arg.arg] = None
        else:
            default_map[arg.arg] = None

    # kwonly defaults: parallel list with None for unset
    for arg, default_node in zip(args.kwonlyargs, args.kw_defaults):
        if default_node is not None:
            try:
                default_map[arg.arg] = ast.unparse(default_node) if hasattr(ast, "unparse") else None
            except Exception:
                default_map[arg.arg] = None
        else:
            default_map[arg.arg] = None

    parameters: List[Dict[str, Any]] = []
    sig_parts: List[str] = []

    def _arg_sig(a: ast.arg) -> str:
        ann = _annotation_to_str(a.annotation)
        part = a.arg
        if ann:
            part = f"{a.arg}: {ann}"
        dflt = default_map.get(a.arg)
        if dflt is not None:
            part = f"{part} = {dflt}"
        return part

    all_positional = args.posonlyargs + args.args
    for a in all_positional:
        sig_parts.append(_arg_sig(a))
        if a.arg not in EXCLUDED_NAMES:
            parameters.append({
                "name": a.arg,
                "annotation": _annotation_to_str(a.annotation),
                "default": default_map.get(a.arg),
            })

    if args.vararg:
        sig_parts.append(f"*{_arg_sig(args.vararg)}")
        parameters.append({
            "name": f"*{args.vararg.arg}",
            "annotation": _annotation_to_str(args.vararg.annotation),
            "default": None,
        })
    elif args.kwonlyargs:
        sig_parts.append("*")

    for a in args.kwonlyargs:
        sig_parts.append(_arg_sig(a))
        parameters.append({
            "name": a.arg,
            "annotation": _annotation_to_str(a.annotation),
            "default": default_map.get(a.arg),
        })

    if args.kwarg:
        sig_parts.append(f"**{_arg_sig(args.kwarg)}")
        parameters.append({
            "name": f"**{args.kwarg.arg}",
            "annotation": _annotation_to_str(args.kwarg.annotation),
            "default": None,
        })

    return_type = _annotation_to_str(node.returns)
    ret_str = f" -> {return_type}" if return_type else ""
    signature = f"{node.name}({', '.join(sig_parts)}){ret_str}"

    return signature, parameters, return_type


class DependencyParser:
    """
    Parses Python code to build a dependency graph between code components.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.components: Dict[str, CodeComponent] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.modules: Set[str] = set()
        
    def parse_repository(self):
        """
        Parse all Python files in the repository to build the dependency graph.
        """
        logger.info(f"Parsing repository at {self.repo_path}")
        
        # First pass: collect all modules and code components
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.repo_path)
                
                # Convert file path to module path
                module_path = self._file_to_module_path(relative_path)
                self.modules.add(module_path)
                
                # Parse the file to collect components
                self._parse_file(file_path, relative_path, module_path)
        
        # Second pass: resolve dependencies
        self._resolve_dependencies()
        
        # Third pass: add class dependencies on methods
        self._add_class_method_dependencies()

        # Fourth pass (V1 Enhancement): extract typed relationships from the same AST info
        self._extract_typed_relationships()
        
        logger.info(f"Found {len(self.components)} code components")
        return self.components
    
    def _file_to_module_path(self, file_path: str) -> str:
        """Convert a file path to a Python module path."""
        # Remove .py extension and convert / to .
        path = file_path[:-3] if file_path.endswith(".py") else file_path
        return path.replace(os.path.sep, ".")
    
    def _parse_file(self, file_path: str, relative_path: str, module_path: str):
        """Parse a single Python file to collect code components."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Add parent field to AST nodes for easier traversal
            add_parent_to_nodes(tree)
            
            # Collect imports
            import_collector = ImportCollector()
            import_collector.visit(tree)
            
            # Collect code components
            self._collect_components(tree, file_path, relative_path, module_path, source)
            
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Error parsing {file_path}: {e}")
    
    def _collect_components(self, tree: ast.AST, file_path: str, relative_path: str, 
                          module_path: str, source: str):
        """Collect all code components (functions, classes, methods) from an AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Class definition
                class_id = f"{module_path}.{node.name}"
                
                # Check if the class has a docstring
                has_docstring = (
                    len(node.body) > 0 
                    and isinstance(node.body[0], ast.Expr) 
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                )
                
                # Extract docstring if it exists
                docstring = self._get_docstring(source, node) if has_docstring else ""
                
                component = CodeComponent(
                    id=class_id,
                    node=node,
                    component_type="class",
                    file_path=file_path,
                    relative_path=relative_path,
                    source_code=self._get_source_segment(source, node),
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    has_docstring=has_docstring,
                    docstring=docstring
                )
                
                self.components[class_id] = component
                
                # Collect methods within the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{class_id}.{item.name}"
                        
                        # Check if the method has a docstring
                        method_has_docstring = (
                            len(item.body) > 0 
                            and isinstance(item.body[0], ast.Expr) 
                            and isinstance(item.body[0].value, ast.Constant)
                            and isinstance(item.body[0].value.value, str)
                        )
                        
                        # Extract docstring if it exists
                        method_docstring = self._get_docstring(source, item) if method_has_docstring else ""
                        
                        # V1 Enhancement: extract function metadata
                        sig, params, ret = _extract_function_metadata(item)

                        method_component = CodeComponent(
                            id=method_id,
                            node=item,
                            component_type="method",
                            file_path=file_path,
                            relative_path=relative_path,
                            source_code=self._get_source_segment(source, item),
                            start_line=item.lineno,
                            end_line=getattr(item, "end_lineno", item.lineno),
                            has_docstring=method_has_docstring,
                            docstring=method_docstring,
                            # V1 Enhancement fields
                            signature=sig,
                            parameters=params,
                            return_type=ret,
                            containing_class=class_id,
                        )
                        
                        self.components[method_id] = method_component
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only collect top-level functions
                if hasattr(node, 'parent') and isinstance(node.parent, ast.Module):
                    func_id = f"{module_path}.{node.name}"
                    
                    # Check if the function has a docstring
                    has_docstring = (
                        len(node.body) > 0 
                        and isinstance(node.body[0], ast.Expr) 
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    )
                    
                    # Extract docstring if it exists
                    docstring = self._get_docstring(source, node) if has_docstring else ""

                    # V1 Enhancement: extract function metadata
                    sig, params, ret = _extract_function_metadata(node)
                    
                    component = CodeComponent(
                        id=func_id,
                        node=node,
                        component_type="function",
                        file_path=file_path,
                        relative_path=relative_path,
                        source_code=self._get_source_segment(source, node),
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        has_docstring=has_docstring,
                        docstring=docstring,
                        # V1 Enhancement fields
                        signature=sig,
                        parameters=params,
                        return_type=ret,
                    )
                    
                    self.components[func_id] = component
    
    def _resolve_dependencies(self):
        """
        Second pass to resolve dependencies between components.
        """
        for component_id, component in self.components.items():
            file_path = component.file_path
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                
                # Parse file to get imports
                tree = ast.parse(source)
                
                # Add parent field to AST nodes for easier traversal
                add_parent_to_nodes(tree)
                
                # Collect imports
                import_collector = ImportCollector()
                import_collector.visit(tree)
                
                # Find the component node in the tree
                component_node = None
                module_path = self._file_to_module_path(component.relative_path)
                
                if component.component_type == "function":
                    # Find top-level function
                    for node in ast.iter_child_nodes(tree):
                        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) 
                                and node.name == component.id.split(".")[-1]):
                            component_node = node
                            break
                
                elif component.component_type == "class":
                    # Find class
                    for node in ast.iter_child_nodes(tree):
                        if isinstance(node, ast.ClassDef) and node.name == component.id.split(".")[-1]:
                            component_node = node
                            break
                
                elif component.component_type == "method":
                    # Find method inside class
                    class_name, method_name = component.id.split(".")[-2:]
                    class_node = None
                    
                    for node in ast.iter_child_nodes(tree):
                        if isinstance(node, ast.ClassDef) and node.name == class_name:
                            class_node = node
                            for item in node.body:
                                if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) 
                                        and item.name == method_name):
                                    component_node = item
                                    break
                            break
                
                if component_node:
                    # Collect dependencies for this specific component
                    dependency_collector = DependencyCollector(
                        import_collector.imports,
                        import_collector.from_imports,
                        module_path,
                        self.modules
                    )
                    
                    # For functions and methods, collect variables defined in the function
                    if isinstance(component_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Add function parameters to local variables
                        for arg in component_node.args.args:
                            dependency_collector.local_variables.add(arg.arg)
                            
                    dependency_collector.visit(component_node)
                    
                    # Add dependencies to the component
                    component.depends_on.update(dependency_collector.dependencies)
                    
                    # Filter out non-existent dependencies
                    component.depends_on = {
                        dep for dep in component.depends_on 
                        if dep in self.components or dep.split(".", 1)[0] in self.modules
                    }
                
            except (SyntaxError, UnicodeDecodeError) as e:
                logger.warning(f"Error analyzing dependencies in {file_path}: {e}")
    
    def _add_class_method_dependencies(self):
        """
        Third pass to make classes dependent on their methods (except __init__).
        """
        # Group components by class
        class_methods = {}
        
        # Collect all methods for each class
        for component_id, component in self.components.items():
            if component.component_type == "method":
                parts = component_id.split(".")
                if len(parts) >= 2:
                    method_name = parts[-1]
                    class_id = ".".join(parts[:-1])
                    
                    if class_id not in class_methods:
                        class_methods[class_id] = []
                    
                    # Don't include __init__ methods as dependencies of the class
                    if method_name != "__init__":
                        class_methods[class_id].append(component_id)
        
        # Add method dependencies to their classes
        for class_id, method_ids in class_methods.items():
            if class_id in self.components:
                class_component = self.components[class_id]
                for method_id in method_ids:
                    class_component.depends_on.add(method_id)

    # ---------------------------------------------------------------------------
    # V1 Enhancement — typed relationship extraction (pass 4)
    # ---------------------------------------------------------------------------

    def _extract_typed_relationships(self):
        """
        Fourth pass: populate each component's `relationships` list with typed
        (source, target, rel_type) entries.

        Relationship types extracted:
          contains     – class → method (ALL methods including __init__), derived
                         from the containing_class field set in pass 1.
                         NOT derived from depends_on, which intentionally excludes
                         __init__ for documentation-ordering purposes.
          imports      – component references an imported symbol in its own AST body
          inherits     – class → direct base class (when base is a known component)
          calls        – function/method → called function/method
          instantiates – function/method → class being instantiated via Call

        The existing `depends_on` set is left unchanged — this pass only writes
        to the new `relationships` field.
        """
        # --- Step 1: contains edges ---
        # Derived from containing_class, which is set on every method during pass 1.
        # This correctly includes __init__, unlike depends_on which excludes it.
        # No depends_on data is used here.
        for comp_id, component in self.components.items():
            if component.component_type == "method" and component.containing_class is not None:
                class_comp = self.components.get(component.containing_class)
                if class_comp is not None:
                    class_comp.relationships.append(
                        TypedRelationship(
                            source=component.containing_class,
                            target=comp_id,
                            rel_type="contains",
                        )
                    )

        # --- Step 2: per-file AST re-traversal for imports, inherits, calls, instantiates ---
        # Group components by file to avoid re-parsing each file more than once.
        by_file: Dict[str, List[str]] = {}
        for comp_id, component in self.components.items():
            by_file.setdefault(component.file_path, []).append(comp_id)

        for file_path, comp_ids in by_file.items():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
                add_parent_to_nodes(tree)

                import_collector = ImportCollector()
                import_collector.visit(tree)

                module_path = self._file_to_module_path(
                    os.path.relpath(file_path, self.repo_path)
                )

                for comp_id in comp_ids:
                    component = self.components[comp_id]
                    self._extract_relationships_for_component(
                        component, tree, source, module_path,
                        import_collector.imports, import_collector.from_imports
                    )
            except (SyntaxError, UnicodeDecodeError, OSError) as e:
                logger.warning(f"Error extracting relationships from {file_path}: {e}")

    def _extract_relationships_for_component(
        self,
        component: "CodeComponent",
        tree: ast.AST,
        source: str,
        module_path: str,
        imports: Set[str],
        from_imports: Dict[str, List[str]],
    ) -> None:
        """
        Populate `component.relationships` with imports, inherits, calls, and
        instantiates edges for one component.

        Args:
            component: The CodeComponent to annotate.
            tree: Full AST of the file containing this component.
            source: Raw source text of the file.
            module_path: Dotted module path of this file.
            imports: Set of bare module names imported with 'import x'.
            from_imports: Dict of module→[names] from 'from x import y'.
        """
        comp_id = component.id

        # Locate the AST node for this component first (needed for all edges below)
        comp_node = self._find_node_in_tree(tree, component)

        # --- imports edges ---
        # Only emit an "imports" edge when the imported name is actually referenced
        # inside this specific component's AST subtree, so the edge is meaningful
        # (not just "this file imports X" duplicated across every component in the file).
        # For classes, scan the entire class body; for functions/methods, scan their node.
        # For file-level imports that aren't used inside any component body, we skip them.
        if comp_node is not None:
            # Collect all Name nodes used inside this component
            used_names: Set[str] = set()
            for n in ast.walk(comp_node):
                if isinstance(n, ast.Name):
                    used_names.add(n.id)
                elif isinstance(n, ast.Attribute):
                    # Capture the root of attribute chains (e.g. module.func → 'module')
                    cur = n
                    while isinstance(cur, ast.Attribute):
                        cur = cur.value
                    if isinstance(cur, ast.Name):
                        used_names.add(cur.id)

            for mod, names in from_imports.items():
                if mod in STANDARD_MODULES:
                    continue
                for name in names:
                    candidate = f"{mod}.{name}"
                    if (
                        candidate in self.components
                        and candidate != comp_id
                        and name in used_names
                        and not any(
                            r.target == candidate and r.rel_type == "imports"
                            for r in component.relationships
                        )
                    ):
                        component.relationships.append(
                            TypedRelationship(source=comp_id, target=candidate, rel_type="imports")
                        )
        if comp_node is None:
            return

        # --- inherits edges (classes only) ---
        if component.component_type == "class" and isinstance(comp_node, ast.ClassDef):
            for base in comp_node.bases:
                base_id = self._resolve_name_to_component_id(base, module_path, imports, from_imports)
                if base_id and base_id in self.components and base_id != comp_id:
                    component.relationships.append(
                        TypedRelationship(source=comp_id, target=base_id, rel_type="inherits")
                    )

        # --- calls and instantiates edges (functions and methods) ---
        if component.component_type in ("function", "method"):
            # Walk Call nodes inside the component body
            for node in ast.walk(comp_node):
                if not isinstance(node, ast.Call):
                    continue

                callee_id = self._resolve_call_to_component_id(
                    node, module_path, imports, from_imports,
                    containing_class=component.containing_class,
                )
                if callee_id is None or callee_id == comp_id:
                    continue
                if callee_id not in self.components:
                    continue

                callee = self.components[callee_id]
                if callee.component_type == "class":
                    rel_type = "instantiates"
                else:
                    rel_type = "calls"

                # Deduplicate: avoid adding the same (source, target, type) twice
                if not any(
                    r.target == callee_id and r.rel_type == rel_type
                    for r in component.relationships
                ):
                    component.relationships.append(
                        TypedRelationship(source=comp_id, target=callee_id, rel_type=rel_type)
                    )

    def _find_node_in_tree(
        self, tree: ast.AST, component: "CodeComponent"
    ) -> Optional[ast.AST]:
        """
        Locate the AST node for a component within a file's AST.

        Args:
            tree: Parsed AST of the file.
            component: The CodeComponent whose node is needed.

        Returns:
            The matching AST node, or None if not found.
        """
        parts = component.id.split(".")
        if component.component_type == "function":
            func_name = parts[-1]
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                    return node
        elif component.component_type == "class":
            class_name = parts[-1]
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    return node
        elif component.component_type == "method":
            class_name = parts[-2]
            method_name = parts[-1]
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                            return item
        return None

    def _resolve_name_to_component_id(
        self,
        name_node: ast.expr,
        module_path: str,
        imports: Set[str],
        from_imports: Dict[str, List[str]],
    ) -> Optional[str]:
        """
        Resolve a simple Name or Attribute AST node to a known component ID.

        Args:
            name_node: An ast.Name or ast.Attribute node.
            module_path: Dotted module path of the current file.
            imports: Set of bare module names from 'import x'.
            from_imports: Dict of module→[names] from 'from x import y'.

        Returns:
            A component ID string if resolvable to a known component, else None.
        """
        if isinstance(name_node, ast.Name):
            name = name_node.id
            if name in BUILTIN_TYPES or name in EXCLUDED_NAMES:
                return None
            # Check from_imports
            for mod, names in from_imports.items():
                if mod in STANDARD_MODULES:
                    continue
                if name in names:
                    return f"{mod}.{name}"
            # Check local module
            local_id = f"{module_path}.{name}"
            if local_id in self.components:
                return local_id
        elif isinstance(name_node, ast.Attribute):
            parts = []
            cur = name_node
            while isinstance(cur, ast.Attribute):
                parts.insert(0, cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.insert(0, cur.id)
                if parts[0] in imports and parts[0] in self.modules and len(parts) > 1:
                    return f"{parts[0]}.{parts[1]}"
        return None

    def _resolve_call_to_component_id(
        self,
        call_node: ast.Call,
        module_path: str,
        imports: Set[str],
        from_imports: Dict[str, List[str]],
        containing_class: Optional[str] = None,
    ) -> Optional[str]:
        """
        Resolve an ast.Call node to a known component ID.

        Handles:
          - Direct calls: ``func()`` → Name node
          - Attribute calls: ``obj.method()`` / ``module.func()`` → Attribute node
          - ``self.method()`` is resolved using the focal component's
            containing_class (e.g. "module.ClassName"), producing the exact ID
            "module.ClassName.method_name".  This avoids false matches when two
            classes in the same module define a method with the same name.

        Args:
            call_node: An ast.Call node.
            module_path: Dotted module path of the current file.
            imports: Set of bare module names from 'import x'.
            from_imports: Dict of module→[names] from 'from x import y'.
            containing_class: Component ID of the class that owns the focal
                component (set when the focal component is a method).

        Returns:
            A component ID string if resolvable to a known component, else None.
        """
        func = call_node.func

        if isinstance(func, ast.Name):
            name = func.id
            if name in BUILTIN_TYPES:
                return None
            # Check from_imports
            for mod, names in from_imports.items():
                if mod in STANDARD_MODULES:
                    continue
                if name in names:
                    candidate = f"{mod}.{name}"
                    if candidate in self.components:
                        return candidate
            # Check local module
            local_id = f"{module_path}.{name}"
            if local_id in self.components:
                return local_id

        elif isinstance(func, ast.Attribute):
            attr_name = func.attr
            value = func.value

            # self.method() — use the focal component's containing_class to
            # produce the exact component ID without any ambiguous suffix search.
            if isinstance(value, ast.Name) and value.id == "self":
                if containing_class is not None:
                    candidate = f"{containing_class}.{attr_name}"
                    if candidate in self.components:
                        return candidate
                return None

            # module.name() or module.Class()
            if isinstance(value, ast.Name):
                prefix = value.id
                if prefix in STANDARD_MODULES:
                    return None
                if prefix in imports and prefix in self.modules:
                    candidate = f"{prefix}.{attr_name}"
                    if candidate in self.components:
                        return candidate
                # from_imports: the value might itself be an imported name
                for mod, names in from_imports.items():
                    if prefix in names:
                        # e.g. from helper import HelperClass; HelperClass.method()
                        candidate = f"{mod}.{prefix}.{attr_name}"
                        if candidate in self.components:
                            return candidate

        return None
    
    def _get_source_segment(self, source: str, node: ast.AST) -> str:
        """Get source code segment for an AST node."""
        try:
            if hasattr(ast, "get_source_segment"):
                segment = ast.get_source_segment(source, node)
                if segment is not None:
                    return segment
            
            # Fallback to manual extraction
            lines = source.split("\n")
            start_line = node.lineno - 1
            end_line = getattr(node, "end_lineno", node.lineno) - 1
            return "\n".join(lines[start_line:end_line + 1])
        
        except Exception as e:
            logger.warning(f"Error getting source segment: {e}")
            return ""
    
    def _get_docstring(self, source: str, node: ast.AST) -> str:
        """Get the docstring for a given AST node."""
        try:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                for item in node.body:
                    if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant):
                        if isinstance(item.value.value, str):
                            return item.value.value
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant):
                        if isinstance(item.value.value, str):
                            return item.value.value
            return ""
        except Exception as e:
            logger.warning(f"Error getting docstring: {e}")
            return ""
    
    def save_dependency_graph(self, output_path: str):
        """
        Save the dependency graph to a JSON file.

        The output format is:
        {
            "components": { <component_id>: { ...component fields... }, ... },
            "relationships": [ { "source": ..., "target": ..., "type": ... }, ... ]
        }

        The "components" section preserves all existing fields (id, component_type,
        file_path, relative_path, depends_on, start_line, end_line, has_docstring,
        docstring) and adds the V1 enhancement fields (signature, parameters,
        return_type, containing_class, source_code).

        The "relationships" section is a flat list of all typed relationships
        across all components, enabling efficient forward and reverse lookup by
        downstream consumers.

        For backwards compatibility the file also maintains the legacy flat
        top-level dict format under the "components" key; existing consumers that
        iterate ``json.load(f).items()`` would need updating, but the key change
        is minimal.
        """
        # Convert to serializable format
        serializable_components = {
            comp_id: component.to_dict()
            for comp_id, component in self.components.items()
        }

        # Collect all relationships into a single flat list
        all_relationships: List[Dict[str, str]] = []
        seen: Set[Tuple[str, str, str]] = set()
        for component in self.components.values():
            for rel in component.relationships:
                key = (rel.source, rel.target, rel.rel_type)
                if key not in seen:
                    seen.add(key)
                    all_relationships.append(rel.to_dict())

        output = {
            "components": serializable_components,
            "relationships": all_relationships,
        }
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Saved dependency graph to {output_path}")
    
    def load_dependency_graph(self, input_path: str):
        """
        Load the dependency graph from a JSON file.

        Supports both the legacy flat format (a dict of component dicts) and
        the new V1 format ({"components": {...}, "relationships": [...]}).
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Detect format: V1 has a "components" key wrapping the component dict
        if "components" in data and isinstance(data["components"], dict):
            serialized_components = data["components"]
        else:
            # Legacy format: top-level keys are component IDs
            serialized_components = data
        
        # Convert back to CodeComponent objects
        self.components = {
            comp_id: CodeComponent.from_dict(comp_data)
            for comp_id, comp_data in serialized_components.items()
        }
        
        logger.info(f"Loaded {len(self.components)} components from {input_path}")
        return self.components


# ---------------------------------------------------------------------------
# V1 Enhancement — RelationshipIndex for efficient forward/reverse lookups
# ---------------------------------------------------------------------------


class RelationshipIndex:
    """
    Builds and exposes forward (outgoing) and reverse (incoming) indexes over
    a flat list of TypedRelationship objects.

    This is intentionally kept separate from DependencyParser so that it can
    be constructed cheaply from any list of relationships (e.g. after loading
    a saved graph) without needing the full parser state.

    Usage::

        parser = DependencyParser(repo_path)
        parser.parse_repository()
        index = RelationshipIndex.from_components(parser.components)

        # What does component A call?
        index.outgoing("module.A", rel_type="calls")

        # Who instantiates class B?
        index.incoming("module.B", rel_type="instantiates")
    """

    def __init__(self, relationships: List[TypedRelationship]) -> None:
        # outgoing[source] = list of TypedRelationship
        self._outgoing: Dict[str, List[TypedRelationship]] = {}
        # incoming[target] = list of TypedRelationship
        self._incoming: Dict[str, List[TypedRelationship]] = {}

        for rel in relationships:
            self._outgoing.setdefault(rel.source, []).append(rel)
            self._incoming.setdefault(rel.target, []).append(rel)

    @classmethod
    def from_components(cls, components: Dict[str, "CodeComponent"]) -> "RelationshipIndex":
        """
        Construct an index from a dict of CodeComponent objects.

        Args:
            components: Dict mapping component ID → CodeComponent.

        Returns:
            A populated RelationshipIndex.
        """
        all_rels: List[TypedRelationship] = []
        seen: Set[Tuple[str, str, str]] = set()
        for component in components.values():
            for rel in component.relationships:
                key = (rel.source, rel.target, rel.rel_type)
                if key not in seen:
                    seen.add(key)
                    all_rels.append(rel)
        return cls(all_rels)

    def outgoing(
        self,
        source_id: str,
        rel_type: Optional[str] = None,
    ) -> List[TypedRelationship]:
        """
        Return relationships originating from *source_id*.

        Args:
            source_id: Component ID of the source.
            rel_type: Optional filter — only return relationships of this type.

        Returns:
            List of matching TypedRelationship objects.
        """
        rels = self._outgoing.get(source_id, [])
        if rel_type is not None:
            rels = [r for r in rels if r.rel_type == rel_type]
        return rels

    def incoming(
        self,
        target_id: str,
        rel_type: Optional[str] = None,
    ) -> List[TypedRelationship]:
        """
        Return relationships targeting *target_id*.

        Args:
            target_id: Component ID of the target.
            rel_type: Optional filter — only return relationships of this type.

        Returns:
            List of matching TypedRelationship objects.
        """
        rels = self._incoming.get(target_id, [])
        if rel_type is not None:
            rels = [r for r in rels if r.rel_type == rel_type]
        return rels

    def all_relationships(self) -> List[TypedRelationship]:
        """Return all relationships in the index (deduplicated)."""
        seen: Set[Tuple[str, str, str]] = set()
        result: List[TypedRelationship] = []
        for rels in self._outgoing.values():
            for rel in rels:
                key = (rel.source, rel.target, rel.rel_type)
                if key not in seen:
                    seen.add(key)
                    result.append(rel)
        return result 