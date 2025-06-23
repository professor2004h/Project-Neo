from typing import Optional, Dict, Any, List
from agentpress.tool import ToolResult, openapi_schema, xml_schema
from sandbox.tool_base import SandboxToolsBase
from agentpress.thread_manager import ThreadManager
from utils.logger import logger
from utils.files_utils import should_exclude_file
import os
import fnmatch
import re

class SandboxPandocTool(SandboxToolsBase):
    """Tool for document format conversion using pypandoc in the sandbox environment.
    
    Supports conversion between various document formats including Markdown, HTML, PDF, DOCX, 
    reStructuredText, LaTeX, EPUB, and plain text. All operations are performed within the 
    sandbox workspace (/workspace).
    """

    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.workspace_path = "/workspace"

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "convert_document",
            "description": (
                "Convert documents between different formats using pypandoc. Supports conversion between "
                "Markdown, HTML, PDF, DOCX, reStructuredText, LaTeX, EPUB, and plain text formats. "
                "\n\n"
                "🚨 IMPORTANT USAGE NOTES:\n"
                "1. PDF Conversion: TeX Live is pre-installed and ready for PDF generation.\n"
                "2. File Paths: All paths are relative to /workspace. For file output, provide "
                "complete paths with filename and extension (e.g., 'documents/output.pdf').\n"
                "3. Content vs File Input: Provide either 'content' for direct text conversion "
                "or 'input_file' for file-based conversion.\n"
                "4. File Output: For advanced formats (PDF, DOCX, EPUB), specify 'output_file' "
                "to save results to disk. Without 'output_file', content is returned as text.\n\n"
                "Supported formats: markdown, html, pdf, docx, rst, latex, epub, txt"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Text content to convert (required if input_file not provided)"
                    },
                    "input_file": {
                        "type": "string", 
                        "description": "Path to input file relative to /workspace (e.g., 'docs/input.md')"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Source format of the content",
                        "default": "markdown",
                        "enum": ["markdown", "html", "pdf", "docx", "rst", "latex", "epub", "txt"]
                    },
                    "output_format": {
                        "type": "string", 
                        "description": "Desired output format",
                        "default": "html",
                        "enum": ["markdown", "html", "pdf", "docx", "rst", "latex", "epub", "txt"]
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Path to save output file relative to /workspace (e.g., 'output/document.pdf'). Required for PDF, DOCX, EPUB formats."
                    },
                    "reference_doc": {
                        "type": "string",
                        "description": "Path to reference document for styling (DOCX output only, relative to /workspace)"
                    }
                },
                "oneOf": [
                    {"required": ["content"]},
                    {"required": ["input_file"]}
                ]
            }
        }
    })
    @xml_schema(
        tag_name="convert-document",
        mappings=[
            {"param_name": "content", "node_type": "element", "path": "content", "required": False},
            {"param_name": "input_file", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "input_format", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "output_format", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "output_file", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "reference_doc", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <function_calls>
        <invoke name="convert_document">
        <parameter name="content"># My Document\n\nThis is a **markdown** document.</parameter>
        <parameter name="input_format">markdown</parameter>
        <parameter name="output_format">html</parameter>
        </invoke>
        </function_calls>
        
        <function_calls>
        <invoke name="convert_document">
        <parameter name="input_file">docs/readme.md</parameter>
        <parameter name="output_format">pdf</parameter>
        <parameter name="output_file">output/readme.pdf</parameter>
        </invoke>
        </function_calls>
        '''
    )
    async def convert_document(
        self, 
        content: Optional[str] = None,
        input_file: Optional[str] = None,
        input_format: str = "markdown",
        output_format: str = "html", 
        output_file: Optional[str] = None,
        reference_doc: Optional[str] = None
    ) -> ToolResult:
        """Convert document content between different formats."""
        
        try:
            # Ensure sandbox is ready
            await self._ensure_sandbox()
            
            # Validate input parameters
            if not content and not input_file:
                return self.fail_response("Either 'content' or 'input_file' must be provided")
            
            if content and input_file:
                return self.fail_response("Provide either 'content' or 'input_file', not both")
            
            # Validate formats
            supported_formats = {'markdown', 'html', 'pdf', 'docx', 'rst', 'latex', 'epub', 'txt'}
            if input_format not in supported_formats:
                return self.fail_response(f"Unsupported input format: '{input_format}'. Supported: {', '.join(supported_formats)}")
            
            if output_format not in supported_formats:
                return self.fail_response(f"Unsupported output format: '{output_format}'. Supported: {', '.join(supported_formats)}")
            
            # Advanced formats require output file
            advanced_formats = {'pdf', 'docx', 'epub'}
            if output_format in advanced_formats and not output_file:
                return self.fail_response(f"output_file is required for {output_format} format")
            
            # Validate reference document
            if reference_doc:
                if output_format != "docx":
                    return self.fail_response("reference_doc parameter is only supported for DOCX output format")
                
                ref_path = self.clean_path(reference_doc)
                full_ref_path = f"{self.workspace_path}/{ref_path}"
                
                if not self._file_exists(full_ref_path):
                    return self.fail_response(f"Reference document not found: {reference_doc}")
            
            # Prepare conversion script
            conversion_script = self._build_conversion_script(
                content=content,
                input_file=input_file,
                input_format=input_format,
                output_format=output_format,
                output_file=output_file,
                reference_doc=reference_doc
            )
            
            # Execute conversion in sandbox
            script_result = self.sandbox.process.exec(
                f"cd {self.workspace_path} && python3 -c \"{conversion_script}\"",
                timeout=120
            )
            
            if script_result.exit_code != 0:
                error_msg = script_result.stderr or script_result.stdout or "Unknown conversion error"
                
                # Special handling for PDF conversion errors
                if "pdf" in output_format.lower() and ("xelatex" in error_msg.lower() or "tex" in error_msg.lower()):
                    return self.fail_response(
                        f"PDF conversion failed: {error_msg}\n\n"
                        "This may be due to complex LaTeX content or formatting issues. You can try:\n"
                        "1. Simplifying the document content\n"
                        "2. Using a different output format (HTML, DOCX)\n" 
                        "3. Converting to HTML first, then using a browser to save as PDF"
                    )
                
                return self.fail_response(f"Document conversion failed: {error_msg}")
            
            # Process results
            if output_file:
                output_path = self.clean_path(output_file)
                full_output_path = f"{self.workspace_path}/{output_path}"
                
                if self._file_exists(full_output_path):
                    message = f"Document successfully converted and saved to: {output_file}"
                    
                    # Add special handling for HTML files 
                    if output_format == "html" and output_file.lower().endswith('.html'):
                        try:
                            website_link = self.sandbox.get_preview_link(8080)
                            website_url = website_link.url if hasattr(website_link, 'url') else str(website_link).split("url='")[1].split("'")[0]
                            message += f"\n\n[HTML file created - you can view it at: {website_url}/{output_path}]"
                        except Exception as e:
                            logger.warning(f"Could not get preview URL: {str(e)}")
                    
                    return self.success_response(message)
                else:
                    return self.fail_response(f"Conversion completed but output file not found: {output_file}")
            else:
                # Return converted content
                output_content = script_result.stdout.strip()
                if not output_content:
                    return self.fail_response("Conversion resulted in empty output")
                
                return self.success_response(
                    f"Document converted from {input_format} to {output_format}:\n\n"
                    f"--- Converted Content ---\n{output_content}\n--- End Content ---\n\n"
                    f"To save this content to a file, specify the 'output_file' parameter in your next conversion request."
                )
            
        except Exception as e:
            logger.error(f"Document conversion error: {str(e)}")
            return self.fail_response(f"Error during document conversion: {str(e)}")

    def _file_exists(self, path: str) -> bool:
        """Check if a file exists in the sandbox."""
        try:
            self.sandbox.fs.get_file_info(path)
            return True
        except Exception:
            return False

    def _is_directory(self, path: str) -> bool:
        """Check if a path is a directory."""
        try:
            file_info = self.sandbox.fs.get_file_info(path)
            return file_info.is_dir
        except Exception:
            return False

    def _validate_path(self, path: str) -> Dict[str, Any]:
        """Validate a file path and return detailed information.
        
        Returns:
            Dict containing validation results with keys:
            - exists: bool
            - is_dir: bool
            - is_file: bool
            - size: int (if file exists)
            - accessible: bool
            - error: str (if any error occurred)
        """
        try:
            full_path = f"{self.workspace_path}/{self.clean_path(path)}"
            file_info = self.sandbox.fs.get_file_info(full_path)
            
            return {
                "exists": True,
                "is_dir": file_info.is_dir,
                "is_file": not file_info.is_dir,
                "size": file_info.size,
                "accessible": True,
                "error": None,
                "path": self.clean_path(path),
                "full_path": full_path
            }
        except Exception as e:
            return {
                "exists": False,
                "is_dir": False,
                "is_file": False,
                "size": 0,
                "accessible": False,
                "error": str(e),
                "path": self.clean_path(path),
                "full_path": f"{self.workspace_path}/{self.clean_path(path)}"
            }

    def _find_files_in_directory(self, directory: str, pattern: str = "*", 
                                include_dirs: bool = False, 
                                recursive: bool = False,
                                exclude_hidden: bool = True) -> List[Dict[str, Any]]:
        """Find files in a directory matching a pattern.
        
        Args:
            directory: Directory path to search in
            pattern: File pattern (supports wildcards like *.md, *.txt)
            include_dirs: Whether to include directories in results
            recursive: Whether to search recursively in subdirectories
            exclude_hidden: Whether to exclude hidden files/directories
            
        Returns:
            List of file info dictionaries
        """
        results = []
        
        try:
            full_dir_path = f"{self.workspace_path}/{self.clean_path(directory)}"
            
            # Check if directory exists
            if not self._is_directory(full_dir_path):
                return results
            
            # List files in directory
            files = self.sandbox.fs.list_files(full_dir_path)
            
            for file_info in files:
                # Skip hidden files if requested
                if exclude_hidden and file_info.name.startswith('.'):
                    continue
                
                # Skip excluded files
                rel_path = f"{self.clean_path(directory)}/{file_info.name}".lstrip('/')
                if should_exclude_file(rel_path):
                    continue
                
                # Check if it matches our criteria
                if file_info.is_dir:
                    if include_dirs and fnmatch.fnmatch(file_info.name, pattern):
                        results.append({
                            "name": file_info.name,
                            "path": rel_path,
                            "full_path": f"{full_dir_path}/{file_info.name}",
                            "is_dir": True,
                            "is_file": False,
                            "size": file_info.size,
                            "type": "directory"
                        })
                    
                    # Recursive search
                    if recursive:
                        sub_results = self._find_files_in_directory(
                            f"{directory}/{file_info.name}",
                            pattern, include_dirs, recursive, exclude_hidden
                        )
                        results.extend(sub_results)
                else:
                    # It's a file
                    if fnmatch.fnmatch(file_info.name, pattern):
                        results.append({
                            "name": file_info.name,
                            "path": rel_path,
                            "full_path": f"{full_dir_path}/{file_info.name}",
                            "is_dir": False,
                            "is_file": True,
                            "size": file_info.size,
                            "type": "file"
                        })
            
        except Exception as e:
            logger.error(f"Error finding files in directory {directory}: {str(e)}")
        
        return results

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "check_file_path",
            "description": (
                "Check if a file or directory path exists and get detailed information about it. "
                "This is useful for validating paths before performing document conversion operations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to check, relative to /workspace (e.g., 'docs/readme.md')"
                    }
                },
                "required": ["path"]
            }
        }
    })
    @xml_schema(
        tag_name="check-file-path",
        mappings=[
            {"param_name": "path", "node_type": "attribute", "path": "."}
        ],
        example='''
        <function_calls>
        <invoke name="check_file_path">
        <parameter name="path">docs/readme.md</parameter>
        </invoke>
        </function_calls>
        '''
    )
    async def check_file_path(self, path: str) -> ToolResult:
        """Check if a file path exists and return detailed information."""
        try:
            await self._ensure_sandbox()
            
            path_info = self._validate_path(path)
            
            if path_info["exists"]:
                file_type = "directory" if path_info["is_dir"] else "file"
                size_info = f" ({path_info['size']} bytes)" if path_info["is_file"] else ""
                
                return self.success_response(
                    f"✅ Path exists: '{path_info['path']}'\n"
                    f"Type: {file_type}{size_info}\n"
                    f"Full path: {path_info['full_path']}"
                )
            else:
                return self.success_response(
                    f"❌ Path does not exist: '{path_info['path']}'\n"
                    f"Full path: {path_info['full_path']}\n"
                    f"Error: {path_info['error']}"
                )
                
        except Exception as e:
            logger.error(f"Error checking file path: {str(e)}")
            return self.fail_response(f"Error checking file path: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "find_files",
            "description": (
                "Find files in the workspace matching specified criteria. "
                "Useful for discovering documents to convert or locating files by pattern."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in, relative to /workspace (default: '.' for root)",
                        "default": "."
                    },
                    "pattern": {
                        "type": "string", 
                        "description": "File pattern to match (supports wildcards like *.md, *.txt, *.docx)",
                        "default": "*"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to search recursively in subdirectories",
                        "default": False
                    },
                    "include_dirs": {
                        "type": "boolean",
                        "description": "Whether to include directories in results",
                        "default": False
                    },
                    "file_extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file extensions to search for (e.g., ['md', 'txt', 'docx'])"
                    }
                },
                "required": []
            }
        }
    })
    @xml_schema(
        tag_name="find-files",
        mappings=[
            {"param_name": "directory", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "pattern", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "recursive", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "include_dirs", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "file_extensions", "node_type": "element", "path": "file_extensions", "required": False}
        ],
        example='''
        <function_calls>
        <invoke name="find_files">
        <parameter name="directory">docs</parameter>
        <parameter name="pattern">*.md</parameter>
        <parameter name="recursive">true</parameter>
        </invoke>
        </function_calls>
        
        <function_calls>
        <invoke name="find_files">
        <parameter name="file_extensions">["md", "txt", "docx"]</parameter>
        <parameter name="recursive">true</parameter>
        </invoke>
        </function_calls>
        '''
    )
    async def find_files(self, directory: str = ".", pattern: str = "*", 
                        recursive: bool = False, include_dirs: bool = False,
                        file_extensions: Optional[List[str]] = None) -> ToolResult:
        """Find files matching specified criteria."""
        try:
            await self._ensure_sandbox()
            
            # Build search patterns based on file extensions
            patterns = []
            if file_extensions:
                for ext in file_extensions:
                    ext = ext.lstrip('.')  # Remove leading dot if present
                    patterns.append(f"*.{ext}")
                    patterns.append(f"*.{ext.upper()}")  # Include uppercase variants
            else:
                patterns = [pattern]
            
            all_results = []
            
            # Search for each pattern
            for search_pattern in patterns:
                results = self._find_files_in_directory(
                    directory, search_pattern, include_dirs, recursive
                )
                all_results.extend(results)
            
            # Remove duplicates based on path
            seen_paths = set()
            unique_results = []
            for result in all_results:
                if result["path"] not in seen_paths:
                    seen_paths.add(result["path"])
                    unique_results.append(result)
            
            if not unique_results:
                search_info = f"pattern '{pattern}'" if not file_extensions else f"extensions {file_extensions}"
                recursive_info = " (recursive)" if recursive else ""
                return self.success_response(
                    f"No files found matching {search_info} in directory '{directory}'{recursive_info}"
                )
            
            # Format results
            results_text = []
            files_count = sum(1 for r in unique_results if r["is_file"])
            dirs_count = sum(1 for r in unique_results if r["is_dir"])
            
            results_text.append(f"Found {files_count} file(s)")
            if include_dirs and dirs_count > 0:
                results_text.append(f" and {dirs_count} directory(ies)")
            results_text.append(f" in '{directory}':")
            
            for result in sorted(unique_results, key=lambda x: (x["is_dir"], x["path"])):
                type_icon = "📁" if result["is_dir"] else "📄"
                size_info = f" ({result['size']} bytes)" if result["is_file"] else ""
                results_text.append(f"\n{type_icon} {result['path']}{size_info}")
            
            return self.success_response(''.join(results_text))
                
        except Exception as e:
            logger.error(f"Error finding files: {str(e)}")
            return self.fail_response(f"Error finding files: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": (
                "List contents of a directory in the workspace. "
                "Useful for exploring directory structure before document conversion."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to list, relative to /workspace (default: '.' for root)",
                        "default": "."
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Whether to show hidden files and directories",
                        "default": False
                    },
                    "show_size": {
                        "type": "boolean", 
                        "description": "Whether to show file sizes",
                        "default": True
                    }
                },
                "required": []
            }
        }
    })
    @xml_schema(
        tag_name="list-directory",
        mappings=[
            {"param_name": "directory", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "show_hidden", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "show_size", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <function_calls>
        <invoke name="list_directory">
        <parameter name="directory">docs</parameter>
        <parameter name="show_size">true</parameter>
        </invoke>
        </function_calls>
        '''
    )
    async def list_directory(self, directory: str = ".", show_hidden: bool = False, 
                           show_size: bool = True) -> ToolResult:
        """List contents of a directory."""
        try:
            await self._ensure_sandbox()
            
            clean_dir = self.clean_path(directory)
            full_path = f"{self.workspace_path}/{clean_dir}"
            
            # Validate directory
            if not self._is_directory(full_path):
                if self._file_exists(full_path):
                    return self.fail_response(f"'{directory}' is a file, not a directory")
                else:
                    return self.fail_response(f"Directory '{directory}' does not exist")
            
            # List directory contents
            files = self.sandbox.fs.list_files(full_path)
            
            if not files:
                return self.success_response(f"Directory '{directory}' is empty")
            
            # Filter and organize results
            dirs = []
            regular_files = []
            
            for file_info in files:
                # Skip hidden files unless requested
                if not show_hidden and file_info.name.startswith('.'):
                    continue
                
                # Skip excluded files
                rel_path = f"{clean_dir}/{file_info.name}".lstrip('/')
                if should_exclude_file(rel_path):
                    continue
                
                if file_info.is_dir:
                    dirs.append(file_info)
                else:
                    regular_files.append(file_info)
            
            # Format output
            result_lines = [f"Contents of directory '{directory}':"]
            
            # List directories first
            if dirs:
                result_lines.append("\n📁 Directories:")
                for dir_info in sorted(dirs, key=lambda x: x.name.lower()):
                    result_lines.append(f"  {dir_info.name}/")
            
            # List files
            if regular_files:
                result_lines.append("\n📄 Files:")
                for file_info in sorted(regular_files, key=lambda x: x.name.lower()):
                    size_info = f" ({file_info.size} bytes)" if show_size else ""
                    result_lines.append(f"  {file_info.name}{size_info}")
            
            if not dirs and not regular_files:
                result_lines.append("\n(No accessible files or directories found)")
            
            return self.success_response('\n'.join(result_lines))
                
        except Exception as e:
            logger.error(f"Error listing directory: {str(e)}")
            return self.fail_response(f"Error listing directory: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "convert_document",
            "description": (
                "Convert documents between different formats using pypandoc. Supports conversion between "
                "Markdown, HTML, PDF, DOCX, reStructuredText, LaTeX, EPUB, and plain text formats. "
                "\n\n"
                "🚨 IMPORTANT USAGE NOTES:\n"
                "1. PDF Conversion: TeX Live is pre-installed and ready for PDF generation.\n"
                "2. File Paths: All paths are relative to /workspace. For file output, provide "
                "complete paths with filename and extension (e.g., 'documents/output.pdf').\n"
                "3. Content vs File Input: Provide either 'content' for direct text conversion "
                "or 'input_file' for file-based conversion.\n"
                "4. File Output: For advanced formats (PDF, DOCX, EPUB), specify 'output_file' "
                "to save results to disk. Without 'output_file', content is returned as text.\n\n"
                "Supported formats: markdown, html, pdf, docx, rst, latex, epub, txt"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Text content to convert (required if input_file not provided)"
                    },
                    "input_file": {
                        "type": "string", 
                        "description": "Path to input file relative to /workspace (e.g., 'docs/input.md')"
                    },
                    "input_format": {
                        "type": "string",
                        "description": "Source format of the content",
                        "default": "markdown",
                        "enum": ["markdown", "html", "pdf", "docx", "rst", "latex", "epub", "txt"]
                    },
                    "output_format": {
                        "type": "string", 
                        "description": "Desired output format",
                        "default": "html",
                        "enum": ["markdown", "html", "pdf", "docx", "rst", "latex", "epub", "txt"]
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Path to save output file relative to /workspace (e.g., 'output/document.pdf'). Required for PDF, DOCX, EPUB formats."
                    },
                    "reference_doc": {
                        "type": "string",
                        "description": "Path to reference document for styling (DOCX output only, relative to /workspace)"
                    }
                },
                "oneOf": [
                    {"required": ["content"]},
                    {"required": ["input_file"]}
                ]
            }
        }
    })
    @xml_schema(
        tag_name="convert-document",
        mappings=[
            {"param_name": "content", "node_type": "element", "path": "content", "required": False},
            {"param_name": "input_file", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "input_format", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "output_format", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "output_file", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "reference_doc", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <function_calls>
        <invoke name="convert_document">
        <parameter name="content"># My Document\n\nThis is a **markdown** document.</parameter>
        <parameter name="input_format">markdown</parameter>
        <parameter name="output_format">html</parameter>
        </invoke>
        </function_calls>
        
        <function_calls>
        <invoke name="convert_document">
        <parameter name="input_file">docs/readme.md</parameter>
        <parameter name="output_format">pdf</parameter>
        <parameter name="output_file">output/readme.pdf</parameter>
        </invoke>
        </function_calls>
        '''
    )
    async def convert_document(
        self, 
        content: Optional[str] = None,
        input_file: Optional[str] = None,
        input_format: str = "markdown",
        output_format: str = "html", 
        output_file: Optional[str] = None,
        reference_doc: Optional[str] = None
    ) -> ToolResult:
        """Convert document content between different formats."""
        
        try:
            # Ensure sandbox is ready
            await self._ensure_sandbox()
            
            # Validate input parameters
            if not content and not input_file:
                return self.fail_response("Either 'content' or 'input_file' must be provided")
            
            if content and input_file:
                return self.fail_response("Provide either 'content' or 'input_file', not both")
            
            # Validate formats
            supported_formats = {'markdown', 'html', 'pdf', 'docx', 'rst', 'latex', 'epub', 'txt'}
            if input_format not in supported_formats:
                return self.fail_response(f"Unsupported input format: '{input_format}'. Supported: {', '.join(supported_formats)}")
            
            if output_format not in supported_formats:
                return self.fail_response(f"Unsupported output format: '{output_format}'. Supported: {', '.join(supported_formats)}")
            
            # Advanced formats require output file
            advanced_formats = {'pdf', 'docx', 'epub'}
            if output_format in advanced_formats and not output_file:
                return self.fail_response(f"output_file is required for {output_format} format")
            
            # Validate input file if provided (using improved validation)
            if input_file:
                input_path_info = self._validate_path(input_file)
                if not input_path_info["exists"]:
                    return self.fail_response(f"Input file not found: {input_file}")
                if input_path_info["is_dir"]:
                    return self.fail_response(f"Input path is a directory, not a file: {input_file}")
            
            # Validate reference document (using improved validation)
            if reference_doc:
                if output_format != "docx":
                    return self.fail_response("reference_doc parameter is only supported for DOCX output format")
                
                ref_path_info = self._validate_path(reference_doc)
                if not ref_path_info["exists"]:
                    return self.fail_response(f"Reference document not found: {reference_doc}")
                if ref_path_info["is_dir"]:
                    return self.fail_response(f"Reference document path is a directory, not a file: {reference_doc}")
            
            # Prepare conversion script
            conversion_script = self._build_conversion_script(
                content=content,
                input_file=input_file,
                input_format=input_format,
                output_format=output_format,
                output_file=output_file,
                reference_doc=reference_doc
            )
            
            # Execute conversion in sandbox
            script_result = self.sandbox.process.exec(
                f"cd {self.workspace_path} && python3 -c \"{conversion_script}\"",
                timeout=120
            )
            
            if script_result.exit_code != 0:
                error_msg = script_result.stderr or script_result.stdout or "Unknown conversion error"
                
                # Special handling for PDF conversion errors
                if "pdf" in output_format.lower() and ("xelatex" in error_msg.lower() or "tex" in error_msg.lower()):
                    return self.fail_response(
                        f"PDF conversion failed: {error_msg}\n\n"
                        "This may be due to complex LaTeX content or formatting issues. You can try:\n"
                        "1. Simplifying the document content\n"
                        "2. Using a different output format (HTML, DOCX)\n" 
                        "3. Converting to HTML first, then using a browser to save as PDF"
                    )
                
                return self.fail_response(f"Document conversion failed: {error_msg}")
            
            # Process results
            if output_file:
                output_path_info = self._validate_path(output_file)
                
                if output_path_info["exists"]:
                    message = f"Document successfully converted and saved to: {output_file}"
                    
                    # Add special handling for HTML files 
                    if output_format == "html" and output_file.lower().endswith('.html'):
                        try:
                            website_link = self.sandbox.get_preview_link(8080)
                            website_url = website_link.url if hasattr(website_link, 'url') else str(website_link).split("url='")[1].split("'")[0]
                            message += f"\n\n[HTML file created - you can view it at: {website_url}/{output_path_info['path']}]"
                        except Exception as e:
                            logger.warning(f"Could not get preview URL: {str(e)}")
                    
                    return self.success_response(message)
                else:
                    return self.fail_response(f"Conversion completed but output file not found: {output_file}")
            else:
                # Return converted content
                output_content = script_result.stdout.strip()
                if not output_content:
                    return self.fail_response("Conversion resulted in empty output")
                
                return self.success_response(
                    f"Document converted from {input_format} to {output_format}:\n\n"
                    f"--- Converted Content ---\n{output_content}\n--- End Content ---\n\n"
                    f"To save this content to a file, specify the 'output_file' parameter in your next conversion request."
                )
            
        except Exception as e:
            logger.error(f"Document conversion error: {str(e)}")
            return self.fail_response(f"Error during document conversion: {str(e)}")

    def _build_conversion_script(
        self,
        content: Optional[str] = None,
        input_file: Optional[str] = None,
        input_format: str = "markdown",
        output_format: str = "html",
        output_file: Optional[str] = None,
        reference_doc: Optional[str] = None
    ) -> str:
        """Build Python script for pypandoc conversion."""
        
        script_lines = [
            "import pypandoc",
            "import sys",
            "import os",
        ]
        
        # Handle input
        if input_file:
            input_path = self.clean_path(input_file)
            script_lines.extend([
                f"input_file = '{input_path}'",
                "if not os.path.exists(input_file):",
                f"    print('Input file not found: {input_file}', file=sys.stderr)",
                "    sys.exit(1)"
            ])
        else:
            # Escape content for Python string
            escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            script_lines.append(f'content = """{escaped_content}"""')
        
        # Build conversion arguments
        extra_args = []
        
        if output_format == "pdf":
            extra_args.extend(['--pdf-engine=xelatex', '-V', 'geometry:margin=1in'])
        
        if reference_doc and output_format == "docx":
            ref_path = self.clean_path(reference_doc)
            extra_args.extend(['--reference-doc', ref_path])
        
        extra_args_str = str(extra_args) if extra_args else "[]"
        
        # Build conversion call
        if output_file:
            output_path = self.clean_path(output_file)
            script_lines.extend([
                f"output_file = '{output_path}'",
                "os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)"
            ])
            
            if input_file:
                script_lines.append(
                    f"pypandoc.convert_file(input_file, '{output_format}', outputfile=output_file, extra_args={extra_args_str})"
                )
            else:
                script_lines.append(
                    f"pypandoc.convert_text(content, '{output_format}', format='{input_format}', outputfile=output_file, extra_args={extra_args_str})"
                )
        else:
            # Convert to string output
            if input_file:
                script_lines.extend([
                    f"result = pypandoc.convert_file(input_file, '{output_format}', extra_args={extra_args_str})",
                    "print(result)"
                ])
            else:
                script_lines.extend([
                    f"result = pypandoc.convert_text(content, '{output_format}', format='{input_format}', extra_args={extra_args_str})",
                    "print(result)"
                ])
        
        return '; '.join(script_lines)

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "list_supported_formats",
            "description": "List all document formats supported by the pandoc conversion tool",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })
    @xml_schema(
        tag_name="list-supported-formats",
        mappings=[],
        example='''
        <function_calls>
        <invoke name="list_supported_formats">
        </invoke>
        </function_calls>
        '''
    )
    async def list_supported_formats(self) -> ToolResult:
        """List all supported document formats and their descriptions."""
        
        formats_info = {
            "markdown": "Markdown - Lightweight markup language with plain text formatting syntax",
            "html": "HTML - HyperText Markup Language for web pages",
            "pdf": "PDF - Portable Document Format (requires TeX Live installation)",
            "docx": "DOCX - Microsoft Word document format",
            "rst": "reStructuredText - Markup syntax and parser component of Docutils",
            "latex": "LaTeX - Document preparation system for high-quality typesetting",
            "epub": "EPUB - Electronic publication format for e-books",
            "txt": "Plain Text - Simple unformatted text format"
        }
        
        format_list = []
        for fmt, description in formats_info.items():
            format_list.append(f"• **{fmt.upper()}**: {description}")
        
        response = (
            "## Supported Document Formats\n\n" +
            "\n".join(format_list) +
            "\n\n**Notes:**\n"
            "- PDF conversion is ready to use with pre-installed TeX Live\n"
            "- DOCX supports reference documents for consistent styling\n"
            "- All formats support both content-to-content and file-to-file conversion\n"
            "- Advanced formats (PDF, DOCX, EPUB) require specifying output_file parameter"
        )
        
        return self.success_response(response) 