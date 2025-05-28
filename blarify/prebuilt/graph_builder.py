from blarify.code_references.lsp_helper import LspQueryHelper
from blarify.graph.graph import Graph
from blarify.graph.graph_environment import GraphEnvironment
from blarify.project_file_explorer.project_files_iterator import ProjectFilesIterator
from blarify.project_graph_creator import ProjectGraphCreator


class GraphBuilder:
    def __init__(
        self,
        root_path: str,
        extensions_to_skip: list[str] = None,
        names_to_skip: list[str] = None,
        only_hierarchy: bool = False,
        graph_environment: GraphEnvironment = None,
        parallel_processing: bool = True,
    ):
        """
        A class responsible for constructing a graph representation of a project's codebase.

        Args:
            root_path: Root directory path of the project to analyze
            extensions_to_skip: File extensions to exclude from analysis (e.g., ['.md', '.txt'])
            names_to_skip: Filenames/directory names to exclude from analysis (e.g., ['venv', 'tests'])
            only_hierarchy: Whether to build only the hierarchy without references
            graph_environment: Custom graph environment
            parallel_processing: Whether to use parallel processing for faster execution

        Example:
            builder = GraphBuilder(
                    "/path/to/project",
                    extensions_to_skip=[".json"],
                    names_to_skip=["__pycache__"],
                    parallel_processing=True
                )
            project_graph = builder.build()

        """

        self.graph_environment = graph_environment or GraphEnvironment("blarify", "repo", root_path)

        self.root_path = root_path
        self.extensions_to_skip = extensions_to_skip or []
        self.names_to_skip = names_to_skip or []
        self.parallel_processing = parallel_processing

        self.only_hierarchy = only_hierarchy

    def build(self) -> Graph:
        lsp_query_helper = self._get_started_lsp_query_helper()
        project_files_iterator = self._get_project_files_iterator()

        graph_creator = ProjectGraphCreator(
            self.root_path, 
            lsp_query_helper, 
            project_files_iterator, 
            graph_environment=self.graph_environment,
            parallel_processing=self.parallel_processing
        )

        if self.only_hierarchy:
            graph = graph_creator.build_hierarchy_only()
        else:
            graph = graph_creator.build()

        lsp_query_helper.shutdown_exit_close()

        return graph

    def _get_project_files_iterator(self):
        return ProjectFilesIterator(
            root_path=self.root_path, extensions_to_skip=self.extensions_to_skip, names_to_skip=self.names_to_skip
        )

    def _get_started_lsp_query_helper(self):
        lsp_query_helper = LspQueryHelper(root_uri=self.root_path)
        lsp_query_helper.start()
        return lsp_query_helper
