from mermaid_tools.tools.base import MermaidTool
from kubiya_sdk.tools import Arg

render_diagram_tool = MermaidTool(
    name="render_mermaid_diagram",
    description="Renders a Mermaid diagram from raw input to a specified output format using mermaid-cli.",
    content="""
#!/bin/bash
set -euo pipefail

# Check if diagram_content is provided
if [ -z "${diagram_content:-}" ]; then
    echo "❌ Error: 'diagram_content' must be provided."
    exit 1
fi

# Validate diagram_content is not empty
if [ -z "$diagram_content" ]; then
    echo "❌ Error: 'diagram_content' is empty."
    exit 1
fi

# Create a temporary input file
INPUT_FILE=$(mktemp /tmp/diagram.XXXXXX.mmd)
echo "$diagram_content" > "$INPUT_FILE"

# Set output file
OUTPUT_FILE="${output_file:-diagram_output.${output_format}}"

# Check if output_format is provided
if [ -z "${output_format:-}" ]; then
    echo "❌ Error: 'output_format' must be provided."
    rm "$INPUT_FILE"
    exit 1
fi

# Validate output_format
VALID_FORMATS=("svg" "png" "pdf")
if [[ ! " ${VALID_FORMATS[@]} " =~ " ${output_format} " ]]; then
    echo "❌ Error: 'output_format' must be one of: ${VALID_FORMATS[*]}"
    rm "$INPUT_FILE"
    exit 1
fi

# Set theme and background options
THEME_OPTION=""
if [ -n "${theme:-}" ]; then
    THEME_OPTION="-t $theme"
fi

BACKGROUND_OPTION=""
if [ -n "${background_color:-}" ]; then
    BACKGROUND_OPTION="-b $background_color"
fi

# Run mermaid-cli command
if ! mmdc -i "$INPUT_FILE" -o "$OUTPUT_FILE" -f "$output_format" $THEME_OPTION $BACKGROUND_OPTION; then
    echo "❌ Error: Failed to render diagram."
    rm "$INPUT_FILE"
    exit 1
fi

echo "✅ Diagram rendered successfully! Output file: $OUTPUT_FILE"

# Clean up temporary file
rm "$INPUT_FILE"
""",
    args=[
        Arg(name="diagram_content", type="str", description="Mermaid diagram content as a string", required=True),
        Arg(name="output_file", type="str", description="Path to the output file", required=False),
        Arg(name="output_format", type="str", description="Output format (svg, png, pdf)", required=True),
        Arg(name="theme", type="str", description="Theme for rendering the diagram (default, dark, forest, neutral)", required=False),
        Arg(name="background_color", type="str", description="Background color or 'transparent'", required=False),
    ],
)