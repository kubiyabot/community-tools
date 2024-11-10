from ..base import MermaidTool
from kubiya_sdk.tools import Arg

convert_markdown_tool = MermaidTool(
    name="convert_markdown_with_diagrams",
    description="Converts a Markdown file containing Mermaid diagrams into a Markdown file with diagrams rendered as images.",
    content="""
    #!/bin/bash
    set -euo pipefail

    if [ -z "${input_markdown:-}" ]; then
        echo "❌ Error: 'input_markdown' must be provided."
        exit 1
    fi

    OUTPUT_MARKDOWN="${output_markdown:-converted_${input_markdown}}"

    # Run mermaid-cli command to transform the Markdown file
    mmdc -i "$input_markdown" -o "$OUTPUT_MARKDOWN"

    echo "✅ Markdown file converted successfully! Output file: $OUTPUT_MARKDOWN"
    """,
    args=[
        Arg(name="input_markdown", type="str", description="Path to the input Markdown file", required=True),
        Arg(name="output_markdown", type="str", description="Path to the output Markdown file", required=False),
    ],
)