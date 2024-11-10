from ..base import MermaidTool
from kubiya_sdk.tools import Arg

convert_markdown_tool = MermaidTool(
    name="convert_markdown_with_diagrams",
    description="Converts Markdown content containing Mermaid diagrams into Markdown with diagrams rendered as images.",
    content="""
#!/bin/bash
set -euo pipefail

# Check if markdown_content is provided
if [ -z "${markdown_content:-}" ]; then
    echo "❌ Error: 'markdown_content' must be provided."
    exit 1
fi

# Validate markdown_content is not empty
if [ -z "$markdown_content" ]; then
    echo "❌ Error: 'markdown_content' is empty."
    exit 1
fi

# Create a temporary input file
INPUT_MARKDOWN_FILE=$(mktemp /tmp/markdown_input.XXXXXX.md)
echo "$markdown_content" > "$INPUT_MARKDOWN_FILE"

# Set output file
OUTPUT_MARKDOWN_FILE="${output_markdown:-converted_markdown.md}"

# Run mermaid-cli command to transform the Markdown content
if ! mmdc -i "$INPUT_MARKDOWN_FILE" -o "$OUTPUT_MARKDOWN_FILE"; then
    echo "❌ Error: Failed to convert Markdown."
    rm "$INPUT_MARKDOWN_FILE"
    exit 1
fi

echo "✅ Markdown converted successfully! Output file: $OUTPUT_MARKDOWN_FILE"

# Clean up temporary file
rm "$INPUT_MARKDOWN_FILE"
""",
    args=[
        Arg(name="markdown_content", type="str", description="Markdown content containing Mermaid diagrams", required=True),
        Arg(name="output_markdown", type="str", description="Path to the output Markdown file", required=False),
    ],
)