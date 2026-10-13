#!/usr/bin/env python3
"""Quick regression check — no LLM calls, pure static analysis."""
import sys, json
sys.path.insert(0, '.')
from src.dependency_analyzer import (
    DependencyParser, RelationshipIndex,
    build_graph_from_components, dependency_first_dfs
)
from collections import Counter

repo = 'data/raw_test_repo_simple'
p = DependencyParser(repo)
p.parse_repository()

print(f"Components: {len(p.components)}")
print("Component IDs:")
for cid in sorted(p.components.keys()):
    print(f"  {cid}")

print()
c = p.components['main.main_function']
print("main.main_function:")
print(f"  signature     : {c.signature}")
print(f"  parameters    : {c.parameters}")
print(f"  return_type   : {c.return_type}")
print(f"  containing_cls: {c.containing_class}")
print(f"  depends_on    : {sorted(c.depends_on)}")
print(f"  relationships :")
for r in c.relationships:
    print(f"    {r.rel_type:12s} -> {r.target}")

print()
c2 = p.components['helper.HelperClass.process_data']
print("helper.HelperClass.process_data:")
print(f"  signature     : {c2.signature}")
print(f"  containing_cls: {c2.containing_class}")
print(f"  relationships :")
for r in c2.relationships:
    print(f"    {r.rel_type:12s} -> {r.target}")

print()
print("Dependency order (first 10):")
graph = build_graph_from_components(p.components)
order = dependency_first_dfs(graph)
for cid in order[:10]:
    print(f"  {cid}")

print()
index = RelationshipIndex.from_components(p.components)
print(f"Total typed relationships: {len(index.all_relationships())}")
print("Relationship type breakdown:")
counts = Counter(r.rel_type for r in index.all_relationships())
for rtype, n in sorted(counts.items()):
    print(f"  {rtype:12s}: {n}")

print()
print("Who calls main.utility_function:")
for r in index.incoming('main.utility_function', rel_type='calls'):
    print(f"  {r.source}")

print()
print("What does processor.AdvancedProcessor.run do:")
for r in index.outgoing('processor.AdvancedProcessor.run'):
    print(f"  {r.rel_type:12s} -> {r.target}")

print()
print("Ordering assertion: utility_function before main_function?", end=" ")
ui = order.index('main.utility_function')
mi = order.index('main.main_function')
print("PASS" if ui < mi else "FAIL")

print("\nDONE")
