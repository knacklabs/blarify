from blarify.code_hierarchy.languages.language_definitions import LanguageDefinitions, IdentifierNodeNotFound
from tree_sitter import Node, Parser, Language
from typing import Dict, Optional, Set
from blarify.graph.node import Node as GraphNode
from blarify.code_hierarchy.languages.FoundRelationshipScope import FoundRelationshipScope
from blarify.graph.node import NodeLabels
from blarify.graph.relationship import RelationshipType

import tree_sitter_kotlin as tskotlin

class KotlinDefinition(LanguageDefinitions):

    secondary_constructor_count = 0

    def get_language_name() -> str:
        return "kotlin"
    
    def get_parsers_for_extensions() -> Dict[str, Parser]:
        return {
            ".kt": Parser(Language(tskotlin.language())),
        }
    
    def should_create_node(node: Node) -> bool:
        return LanguageDefinitions._should_create_node_base_implementation(
            node,
            [
                "function_declaration",
                "class_declaration",
                "primary_constructor",
                "secondary_constructor",
            ],
        )

    def get_identifier_node(node: Node) -> Node:
        if node.type == "secondary_constructor":
            KotlinDefinition.secondary_constructor_count += 1
            for child in node.children:
                if child.type == "constructor":
                    return child

        res = KotlinDefinition._get_identifier_node_base_implementation(node)
        return res

    def get_body_node(node: Node) -> Node:
        return LanguageDefinitions._get_body_node_base_implementation(node)

    def get_relationship_type(node: GraphNode, node_in_point_reference: Node) -> Optional[FoundRelationshipScope]:
        return KotlinDefinition._find_relationship_type(
            node_label=node.label,
            node_in_point_reference=node_in_point_reference,
        )

    def get_node_label_from_type(type: str) -> NodeLabels:
        return {
            "class_declaration": NodeLabels.CLASS,
            "function_declaration": NodeLabels.FUNCTION,
            "primary_constructor": NodeLabels.FUNCTION,
            "secondary_constructor": NodeLabels.FUNCTION,
        }[type]
    
    @staticmethod
    def get_identifier_name(identifier_node: Node) -> str:
        
        if identifier_node.type == "primary_constructor":
            return "primary_constructor"

        if identifier_node.type == "constructor":
            return f"constructor_{KotlinDefinition.secondary_constructor_count}"

        return identifier_node.text.decode("utf-8")
    
    def get_language_file_extensions() -> Set[str]:
        return {".kt"}
    
    def _find_relationship_type(node_label: str, node_in_point_reference: Node) -> Optional[FoundRelationshipScope]:
        relationship_types = KotlinDefinition._get_relationship_types_by_label()
        relevant_relationship_types = relationship_types.get(node_label, {})

        return LanguageDefinitions._traverse_and_find_relationships(
            node_in_point_reference, relevant_relationship_types
        )
    
    def _get_relationship_types_by_label() -> dict[str, RelationshipType]:
        return {
            NodeLabels.CLASS: {
                "object_creation_expression": RelationshipType.INSTANTIATES,
                "using_directive": RelationshipType.IMPORTS,
                "variable_declaration": RelationshipType.TYPES,
                "parameter": RelationshipType.TYPES,
                "base_list": RelationshipType.INHERITS,
            },
            NodeLabels.FUNCTION: {
                "invocation_expression": RelationshipType.CALLS,
            },
        }

    @staticmethod
    def _get_identifier_node_base_implementation(node: Node) -> Node:
        if(node.type == "primary_constructor"):
            return node;
    
        return LanguageDefinitions._get_identifier_node_base_implementation(node)