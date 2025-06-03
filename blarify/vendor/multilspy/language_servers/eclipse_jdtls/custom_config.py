"""
Custom configurations for Eclipse JDTLS to fix workspace and reference issues
"""

import os
import json
from pathlib import Path


def get_fixed_initialize_params(base_params: dict) -> dict:
    """
    Apply fixes to the Eclipse JDTLS initialization parameters to resolve
    issues with large Java projects like nacos-java.
    """
    # Create a deep copy to avoid modifying the original
    params = json.loads(json.dumps(base_params))
    
    # Fix 1: Increase memory allocation to match what's in the command line
    params["initializationOptions"]["settings"]["java"]["jdt"]["ls"]["vmargs"] = (
        "-XX:+UseParallelGC -XX:GCTimeRatio=4 -XX:AdaptiveSizePolicyWeight=90 "
        "-Dsun.zip.disableMemoryMapping=true -Xmx3G -Xms100m -Xlog:disable"
    )
    
    # Fix 2: Add exclusions for generated files and build directories
    params["initializationOptions"]["settings"]["java"]["import"]["exclusions"] = [
        "**/node_modules/**",
        "**/.metadata/**",
        "**/archetype-resources/**",
        "**/META-INF/maven/**",
        "**/target/**",  # Exclude Maven build directory
        "**/build/**",   # Exclude Gradle build directory
        "**/bin/**",     # Exclude compiled output
        "**/out/**",     # Exclude IDE output directories
        "**/.git/**",    # Exclude git directory
        "**/generated-sources/**",  # Exclude generated sources
        "**/generated-test-sources/**"  # Exclude generated test sources
    ]
    
    # Fix 3: Change updateBuildConfiguration to automatic
    params["initializationOptions"]["settings"]["java"]["configuration"]["updateBuildConfiguration"] = "automatic"
    
    # Fix 4: Disable autobuild temporarily to avoid conflicts
    params["initializationOptions"]["settings"]["java"]["autobuild"]["enabled"] = False
    
    # Fix 5: Add resource filters to ignore build directories
    params["initializationOptions"]["settings"]["java"]["project"]["resourceFilters"] = [
        "node_modules",
        "\\.git",
        "target",
        "build", 
        "bin",
        "out",
        "generated-sources",
        "generated-test-sources"
    ]
    
    # Fix 6: Increase concurrent builds to handle large projects
    params["initializationOptions"]["settings"]["java"]["maxConcurrentBuilds"] = 4
    
    # Fix 7: Adjust timeout for JDWP requests
    params["initializationOptions"]["settings"]["java"]["debug"]["settings"]["jdwp"]["requestTimeout"] = 10000
    
    # Fix 8: Enable shared indexes for better performance
    params["initializationOptions"]["settings"]["java"]["sharedIndexes"]["enabled"] = "on"
    
    return params


def get_persistent_workspace_dir(repository_path: str) -> str:
    """
    Get a persistent workspace directory based on the repository path
    instead of creating a new UUID-based directory each time.
    """
    import hashlib
    from blarify.vendor.multilspy.multilspy_settings import MultilspySettings
    from pathlib import PurePath
    
    # Create a stable hash of the repository path
    repo_hash = hashlib.md5(repository_path.encode()).hexdigest()[:12]
    repo_name = os.path.basename(repository_path)
    
    # Use a combination of repo name and hash for uniqueness
    workspace_id = f"{repo_name}-{repo_hash}"
    
    ws_dir = str(
        PurePath(
            MultilspySettings.get_language_server_directory(),
            "EclipseJDTLS",
            "workspaces",
            workspace_id
        )
    )
    
    return ws_dir


def should_exclude_file(file_path: str) -> bool:
    """
    Check if a file should be excluded from LSP operations based on its path.
    This helps avoid processing generated files that cause issues.
    """
    exclude_patterns = [
        '/target/',
        '/build/',
        '/generated-sources/',
        '/generated-test-sources/',
        '/bin/',
        '/out/',
        '/.git/',
        '/node_modules/',
        '/.metadata/'
    ]
    
    normalized_path = file_path.replace('\\', '/')
    
    for pattern in exclude_patterns:
        if pattern in normalized_path:
            return True
    
    return False 