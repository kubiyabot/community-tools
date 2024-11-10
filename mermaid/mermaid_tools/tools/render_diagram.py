from mermaid_tools.base import MermaidTool
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools import tool_registry

render_diagram_tool = MermaidTool(
    name="render_mermaid_diagram",
    description="Renders a Mermaid diagram from raw input to a specified output format using mermaid-cli.",
    content="""
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
TEMP_DIR=$(mktemp -d)
INPUT_FILE="$TEMP_DIR/diagram.mmd"
echo "$diagram_content" > "$INPUT_FILE"

# Set output file
OUTPUT_FILE="${output_file:-diagram_output.${output_format}}"

# Check if output_format is provided
if [ -z "${output_format:-}" ]; then
    echo "❌ Error: 'output_format' must be provided."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Validate output_format
VALID_FORMATS="svg png pdf"
if ! echo "$VALID_FORMATS" | grep -wq "$output_format"; then
    echo "❌ Error: 'output_format' must be one of: $VALID_FORMATS"
    rm -rf "$TEMP_DIR"
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
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "✅ Diagram rendered successfully! Output file: $OUTPUT_FILE"

# Clean up temporary files
rm -rf "$TEMP_DIR"
""",
    args=[
        Arg(name="diagram_content", type="str", description="Mermaid diagram content as a string", required=True),
        Arg(name="output_file", type="str", description="Path to the output file", required=False),
        Arg(name="output_format", type="str", description="Output format (svg, png, pdf)", required=True),
        Arg(name="theme", type="str", description="Theme for rendering the diagram (default, dark, forest, neutral)", required=False),
        Arg(name="background_color", type="str", description="Background color or 'transparent'", required=False),
    ],
)

tool_registry.register("mermaid", render_diagram_tool)
