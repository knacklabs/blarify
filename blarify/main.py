from blarify.project_graph_creator import ProjectGraphCreator
from blarify.project_file_explorer import ProjectFilesIterator
from blarify.project_file_explorer import ProjectFileStats
from blarify.project_graph_updater import ProjectGraphUpdater
from blarify.project_graph_diff_creator import ChangeType, FileDiff, PreviousNodeState, ProjectGraphDiffCreator
from blarify.db_managers.neo4j_manager import Neo4jManager
from blarify.code_references import LspQueryHelper
from blarify.graph.graph_environment import GraphEnvironment
from blarify.utils.file_remover import FileRemover
import time

import dotenv
import os

import logging

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


def main(root_path: str = None, blarignore_path: str = None):
    lsp_query_helper = LspQueryHelper(root_uri=root_path)

    lsp_query_helper.start()

    project_files_iterator = ProjectFilesIterator(
        root_path=root_path, blarignore_path=blarignore_path, extensions_to_skip=[".json", ".xml"]
    )

    ProjectFileStats(project_files_iterator).print(limit=10)

    FileRemover.soft_delete_if_exists(root_path, "Gemfile")

    repoId = "test"
    entity_id = "test"
    graph_manager = Neo4jManager(repoId, entity_id)

    graph_creator = ProjectGraphCreator(root_path, lsp_query_helper, project_files_iterator)

    graph = graph_creator.build()

    relationships = graph.get_relationships_as_objects()
    nodes = graph.get_nodes_as_objects()

    print(f"Saving graph with {len(nodes)} nodes and {len(relationships)} relationships")
    graph_manager.save_graph(nodes, relationships)
    graph_manager.close()

    lsp_query_helper.shutdown_exit_close()


def main_diff(file_diffs: list, root_uri: str = None, blarignore_path: str = None, repoId: str = None, entity_id: str = None, 
              graph_environment_name: str = None, 
              pr_environment_name: str = None,
              pr_number: str = None):
    lsp_query_helper = LspQueryHelper(root_uri=root_uri)
    lsp_query_helper.start()

    project_files_iterator = ProjectFilesIterator(
        root_path=root_uri,
        blarignore_path=blarignore_path,
    )

    graph_manager = Neo4jManager(repoId, entity_id)

    graph_diff_creator = ProjectGraphDiffCreator(
        root_path=root_uri,
        lsp_query_helper=lsp_query_helper,
        project_files_iterator=project_files_iterator,
        file_diffs=file_diffs,
        graph_environment=GraphEnvironment(graph_environment_name, "repo", root_uri),
        pr_environment=GraphEnvironment(pr_environment_name, pr_number, root_uri),
    )

    start = time.perf_counter()

    graph = graph_diff_creator.build()

    end = time.perf_counter()
    print(f"Time taken: {end - start} seconds")

    relationships = graph.get_relationships_as_objects()
    nodes = graph.get_nodes_as_objects()

    for node in nodes:
        __convert_path_to_relative_path(node, root_uri)

    print(f"Saving graph with {len(nodes)} nodes and {len(relationships)} relationships")
    graph_manager.save_graph(nodes, relationships)
    graph_manager.close()
    lsp_query_helper.shutdown_exit_close()


def __convert_path_to_relative_path(node: dict, root_path: str):
        """
        Converts an absolute file path in the node's 'attributes.path' to a relative path 
        with respect to the configured root path.
        This method modifies the input node in place. If the 'path' attribute is missing 
        or empty, the method does nothing. If the path starts with 'file://', that prefix 
        is removed before conversion.
        Example:
            Given:
                node["attributes"]["path"] = "file:///user/hitesh/code-review/src/config.ts"
                self.config.root_path = "/user/hitesh/code-review"
            Result:
                node["attributes"]["path"] = "src/config.ts"
        Args:
            node (dict): A dictionary representing a node, expected to contain an 
                        'attributes' key with a 'path' subkey.
        Returns:
            None
        """
        absolutePath = node.get("attributes", {}).get("path", "")

        if not absolutePath:
            return

        if absolutePath.startswith('file://'):
            absolutePath = absolutePath.replace('file://', '')
            node["attributes"]["path"] = '/' + os.path.relpath(absolutePath, root_path)



def main_update(updated_files: list, root_uri: str = None, blarignore_path: str = None):
    lsp_query_helper = LspQueryHelper(root_uri=root_uri)
    lsp_query_helper.start()

    project_files_iterator = ProjectFilesIterator(
        root_path=root_uri,
        blarignore_path=blarignore_path,
    )

    repoId = "test"
    entity_id = "test"
    graph_manager = Neo4jManager(repoId, entity_id)

    delete_updated_files_from_neo4j(updated_files, graph_manager)

    graph_diff_creator = ProjectGraphUpdater(
        updated_files=updated_files,
        root_path=root_uri,
        lsp_query_helper=lsp_query_helper,
        project_files_iterator=project_files_iterator,
        graph_environment=GraphEnvironment("dev", "MAIN", root_uri),
    )

    graph = graph_diff_creator.build()

    relationships = graph.get_relationships_as_objects()
    nodes = graph.get_nodes_as_objects()

    print(f"Saving graph with {len(nodes)} nodes and {len(relationships)} relationships")
    graph_manager.save_graph(nodes, relationships)
    graph_manager.close()
    lsp_query_helper.shutdown_exit_close()


def delete_updated_files_from_neo4j(updated_files, db_manager: Neo4jManager):
    for updated_file in updated_files:
        db_manager.detatch_delete_nodes_with_path(updated_file.path)


def main_diff_with_previous(
    file_diffs: list,
    root_uri: str = None,
    blarignore_path: str = None,
    previous_node_states: list[PreviousNodeState] = None,
):
    lsp_query_helper = LspQueryHelper(root_uri=root_uri)
    lsp_query_helper.start()

    project_files_iterator = ProjectFilesIterator(
        root_path=root_uri,
        blarignore_path=blarignore_path,
    )

    repoId = "test"
    entity_id = "test"
    graph_manager = Neo4jManager(repoId, entity_id)

    graph_diff_creator = ProjectGraphDiffCreator(
        root_path=root_uri,
        lsp_query_helper=lsp_query_helper,
        project_files_iterator=project_files_iterator,
        file_diffs=file_diffs,
        graph_environment=GraphEnvironment("dev", "MAIN", root_uri),
        pr_environment=GraphEnvironment("dev", "pr-123", root_uri),
    )

    graph = graph_diff_creator.build_with_previous_node_states(previous_node_states=previous_node_states)

    relationships = graph.get_relationships_as_objects()
    nodes = graph.get_nodes_as_objects()

    print(f"Saving graph with {len(nodes)} nodes and {len(relationships)} relationships")

    # batch create nodes and relationships

    graph_manager.save_graph(nodes, relationships)
    graph_manager.close()
    lsp_query_helper.shutdown_exit_close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dotenv.load_dotenv()
    root_path = "/Users/hitesh/workspace/java-code-pr/PR/java-code"
    blarignore_path = "/Users/cawdev/Desktop/blarify/.blarignore"
    # main(root_path=root_path, blarignore_path=blarignore_path)

    file_diffs = [
        FileDiff(
            path=f"file://{root_path}/ArrayGenerator.java",
            diff_text="diff++",
            change_type=ChangeType.MODIFIED,
        ),
        FileDiff(
            path=f"file://{root_path}/ArrayProcessor.java",
            diff_text="diff++",
            change_type=ChangeType.MODIFIED,
        ),
        FileDiff(
            path=f"file://{root_path}/ArrayProcessor2.java",
            diff_text="diff++",
            change_type=ChangeType.DELETED,
        ),
    ]

    main_diff(
        file_diffs=file_diffs,
        root_uri=root_path,
        repoId="",
        entity_id="jayanth",
        graph_environment_name="blarify",
        pr_environment_name="blarify",
        pr_number="123",
    )

    print("Updating")
    # main_update(
    #     updated_files=[
    #         # UpdatedFile("file:///temp/repos/development/main/0/encuadrado-web/encuadrado-web/schemas.py"),
    #         # UpdatedFile("file:///temp/repos/development/main/0/encuadrado-web/encuadrado-web/models.py"),
    #     ],
    #     root_uri=root_path,
    #     blarignore_path=blarignore_path,
    # )
    # main_update(
    #     updated_files=[
    #         UpdatedFile("file:///temp/repos/development/main/0/encuadrado-web/encuadrado-web/schemas.py"),
    #         UpdatedFile("file:///temp/repos/development/main/0/encuadrado-web/encuadrado-web/models.py"),
    #     ],
    #     root_uri=root_path,
    #     blarignore_path=blarignore_path,
    # )

    # main_diff_with_previous(
    #     file_diffs=[
    #         FileDiff(
    #             path="file:///home/juan/devel/blar/blar-qa/blar/agents/tasks.py",
    #             diff_text="diff+++",
    #             change_type=ChangeType.MODIFIED,
    #         ),
    #     ],
    #     root_uri=root_path,
    #     blarignore_path=blarignore_path,
    #     previous_node_states=[
    #         PreviousNodeState(
    #             "/dev/MAIN/blar-qa/blar/agents/tasks.py.execute_pr_report_agent_task",
    #             open("/home/juan/devel/blar/lsp-poc/blarify/example", "r").read(),
    #         ),
    #         PreviousNodeState(
    #             "/dev/MAIN/blar-qa/blar/agents/tasks.py.execute_pr_report_agent_taski",
    #             open("/home/juan/devel/blar/lsp-poc/blarify/example", "r").read(),
    #         ),
    #     ],
    # )
