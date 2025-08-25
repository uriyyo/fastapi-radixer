from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rich.tree import Tree
from starlette.routing import Route

from ._base import RadixerRoutingTable
from .parser import param_priority_key, parse_param_part
from .types import (
    Method,
    Methods,
    ParamRouteDecl,
    ParamType,
    Path,
    PathPart,
    RouteDecl,
    StaticRouteDecl,
    is_param_path_part,
    is_param_route,
    is_static_path_part,
    is_static_route,
)


@dataclass
class LookupResult:
    route_decl: RouteDecl
    args: list[Any]


@dataclass
class RoutingTrie:
    methods: Methods = field(default_factory=set)

    leafs: list[ParamRouteDecl] = field(default_factory=list)

    static_parts: dict[Path, RoutingTrie] = field(default_factory=dict)
    param_parts: dict[ParamType, RoutingTrie] = field(default_factory=dict)

    radix_node: tuple[Path, RoutingTrie] | None = None

    def dump(self, tree: Tree) -> None:
        if self.radix_node:
            path, node = self.radix_node
            sub_tree = tree.add(path)
            node.dump(sub_tree)
            return

        for path, node in self.static_parts.items():
            sub_tree = tree.add(path)
            node.dump(sub_tree)

        for param_type, node in self.param_parts.items():
            sub_tree = tree.add(f"{{{param_type}}}")
            node.dump(sub_tree)

    def prepare_trie(self) -> None:
        self.param_parts = {k: self.param_parts[k] for k in sorted(self.param_parts, key=param_priority_key)}

        for trie in self.param_parts.values():
            trie.prepare_trie()

        for trie in self.static_parts.values():
            trie.prepare_trie()

        if self.param_parts:
            return

        if self.leafs:
            return

        if len(self.static_parts) != 1:
            return

        ((path, trie),) = self.static_parts.items()

        if next_node := trie.radix_node:
            subpath, subnode = next_node
            self.radix_node = f"{path}/{subpath}", subnode
        else:
            self.radix_node = path, trie

    def add_route(self, route: ParamRouteDecl, parts: list[PathPart]) -> None:
        self.methods.update(route["methods"])

        if not parts:
            self.leafs.append(route)
            return

        part, *rest = parts

        if is_static_path_part(part):
            if part["path"] not in self.static_parts:
                self.static_parts[part["path"]] = RoutingTrie()

            self.static_parts[part["path"]].add_route(route, rest)
        elif is_param_path_part(part):
            if part["type"] not in self.param_parts:
                self.param_parts[part["type"]] = RoutingTrie()

            self.param_parts[part["type"]].add_route(route, rest)
        else:
            raise ValueError("Unknown path part type")

    def _leaf_lookup(self, method: Method) -> LookupResult | None:
        for leaf in self.leafs:
            if method in leaf["methods"]:
                return LookupResult(
                    route_decl=leaf,
                    args=[],
                )

        return None

    def _radix_lookup(self, method: Method, path: Path) -> LookupResult | None:
        if node := self.radix_node:
            subpath, subnode = node

            if path.startswith(subpath):
                return subnode.lookup(method, path[len(subpath) + 1 :])

        return None

    def _static_lookup(self, method: Method, part: Path, rest: Path) -> LookupResult | None:
        if trie := self.static_parts.get(part):
            return trie.lookup(method, rest)

        return None

    def _param_lookup(self, method: Method, part: Path, rest: Path) -> LookupResult | None:
        for param_type, trie in self.param_parts.items():
            is_valid, parsed = parse_param_part(param_type, part)

            if not is_valid:
                continue

            if res := trie.lookup(method, rest):
                res.args.insert(0, parsed)
                return res

        return None

    def lookup(self, method: Method, path: Path) -> LookupResult | None:
        if not path:
            return self._leaf_lookup(method)

        if self.radix_node:
            return self._radix_lookup(method, path)

        try:
            part, rest = path.split("/", maxsplit=1)
        except ValueError:
            part, rest = path, ""

        if res := self._static_lookup(method, part, rest):
            return res

        if res := self._param_lookup(method, part, rest):
            return res

        return None


@dataclass
class RoutingTable(RadixerRoutingTable):
    route_trie: RoutingTrie = field(default_factory=RoutingTrie)
    static_routes: dict[tuple[str, Method], StaticRouteDecl] = field(default_factory=dict)

    trie_prepared: bool = False

    def dump(self, tree: Tree) -> None:
        for path, _ in self.static_routes:
            tree.add(path)

        self.route_trie.dump(tree)

    def prepare(self) -> None:
        if self.trie_prepared:
            return

        self.route_trie.prepare_trie()
        self.trie_prepared = True

    def add_static_route(self, route: StaticRouteDecl) -> None:
        for method in route["methods"]:
            self.static_routes[(route["path"], method)] = route

    def add_param_route(self, route: ParamRouteDecl) -> None:
        self.route_trie.add_route(route, route["parts"])

    def add_route(self, route: RouteDecl) -> None:
        if is_static_route(route):
            self.add_static_route(route)
        elif is_param_route(route):
            self.add_param_route(route)
        else:
            raise ValueError("route must be static or param")

    def lookup(self, method: Method, path: Path) -> tuple[Route, dict[str, Any]] | None:
        if res := self.static_routes.get((path, method)):
            return res["route"], {}

        if res := self.route_trie.lookup(method, path):
            route = res.route_decl["route"]
            params = {p: res.args[i] for i, p in enumerate(res.route_decl["params"])}

            return route, params

        return None


__all__ = [
    "RoutingTable",
    "RoutingTrie",
]
