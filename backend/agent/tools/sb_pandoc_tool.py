from typing import Optional, Dict, Any
from agentpress.tool import ToolResult, openapi_schema, xml_schema
from sandbox.tool_base import SandboxToolsBase
from agentpress.thread_manager import ThreadManager
from utils.logger import logger
import os

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