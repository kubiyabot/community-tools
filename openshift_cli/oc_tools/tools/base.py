# oc_tools/tools/base.py
from kubiya_sdk.tools import Tool, Arg, FileSpec

OPENSHIFT_ICON_URL = "https://dwglogo.com/wp-content/uploads/2017/11/2200px_OpenShift_logo.png"

class OpenShiftTool(Tool):
    def __init__(self, name, description, content, args, image="openshift/origin-cli:latest"):
        # Add OpenShift context setup and helper functions
        inject_openshift_context = """
# Begin OpenShift context setup
{
    # Define locations for service account files
    TOKEN_LOCATION="/tmp/openshift_context_token"
    CERT_LOCATION="/tmp/openshift_context_cert"

    # Verify required files exist and are readable
    if [ ! -f "$TOKEN_LOCATION" ]; then
        echo "❌ Error: OpenShift token file not found at $TOKEN_LOCATION" >&2
        exit 1
    fi

    if [ ! -f "$CERT_LOCATION" ]; then
        echo "❌ Error: OpenShift certificate file not found at $CERT_LOCATION" >&2
        exit 1
    fi

    if [ ! -r "$TOKEN_LOCATION" ]; then
        echo "❌ Error: OpenShift token file is not readable at $TOKEN_LOCATION" >&2
        exit 1
    fi

    if [ ! -r "$CERT_LOCATION" ]; then
        echo "❌ Error: OpenShift certificate file is not readable at $CERT_LOCATION" >&2
        exit 1
    fi

    # Read token securely
    OPENSHIFT_TOKEN=$(cat "$TOKEN_LOCATION")
    if [ -z "$OPENSHIFT_TOKEN" ]; then
        echo "❌ Error: OpenShift token file is empty" >&2
        exit 1
    fi

    # Configure oc with proper error handling
    echo "🔧 Configuring OpenShift context..."

    if ! oc config set-cluster in-cluster --server=https://kubernetes.default.svc \\
                                          --certificate-authority="$CERT_LOCATION" >/dev/null 2>&1; then
        echo "❌ Error: Failed to set OpenShift cluster configuration" >&2
        exit 1
    fi

    if ! oc config set-credentials in-cluster --token="$OPENSHIFT_TOKEN" >/dev/null 2>&1; then
        echo "❌ Error: Failed to set OpenShift credentials" >&2
        exit 1
    fi

    if ! oc config set-context in-cluster --cluster=in-cluster --user=in-cluster >/dev/null 2>&1; then
        echo "❌ Error: Failed to set OpenShift context" >&2
        exit 1
    fi

    if ! oc config use-context in-cluster >/dev/null 2>&1; then
        echo "❌ Error: Failed to switch to in-cluster context" >&2
        exit 1
    fi

    # Verify connection
    if ! oc cluster-info >/dev/null 2>&1; then
        echo "❌ Error: Failed to verify OpenShift cluster connection" >&2
        exit 1
    fi

    echo "✅ Successfully configured OpenShift context"
}
"""

        helper_functions = """
# Begin helper functions
{
    # Set global constants
    export MAX_ITEMS=50
    export MAX_OUTPUT_WIDTH=120
    export MAX_LOGS=1000

    # Truncation helper functions
    truncate_output() {
        local max_items=${1:-$MAX_ITEMS}
        local max_width=${2:-$MAX_OUTPUT_WIDTH}
        
        awk -v max_items="$max_items" -v max_width="$max_width" '
        NR <= max_items {
            if (length($0) > max_width) {
                print substr($0, 1, max_width-3) "..."
            } else {
                print
            }
        }
        NR == max_items+1 {
            print "... output truncated ..."
        }
        '
    }

    # Wrapper for oc commands with truncation and improved error handling
    oc_with_truncation() {
        local cmd="$1"
        local max_items=${2:-$MAX_ITEMS}
        local max_width=${3:-$MAX_OUTPUT_WIDTH}
        
        if [ -z "$cmd" ]; then
            echo "❌ Error: Command is required" >&2
            return 1
        fi
        
        # Validate numeric parameters
        case "$max_items" in
            ''|*[!0-9]*) 
                echo "❌ Error: max_items must be a positive integer" >&2
                return 1
                ;;
        esac
        case "$max_width" in
            ''|*[!0-9]*) 
                echo "❌ Error: max_width must be a positive integer" >&2
                return 1
                ;;
        esac
        
        eval "$cmd" | truncate_output "$max_items" "$max_width"
        return ${PIPESTATUS[0]}
    }
}
"""
        # Combine scripts with proper line endings
        full_content = (
            "# Begin OpenShift context setup\\n"
            f"{inject_openshift_context}\\n\\n"
            "# Begin helper functions\\n"
            f"{helper_functions}\\n\\n"
            "# Begin main script\\n"
            f"{content}\\n"
        )

        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/openshift_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/openshift_context_cert"
            )
        ]

        super().__init__(
            name=name,
            description=description,
            icon_url=OPENSHIFT_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            with_files=file_specs,
        )
