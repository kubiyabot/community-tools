from kubiya_sdk.tools import Arg
from .base import GrypeTool

def create_scan_image_tool():
    args = [
        Arg("image", description="The container image to scan", type=str),
        Arg("fail_on", description="Exit with error code if vulnerability found with severity >= specified level (negligible, low, medium, high, critical)", type=str, required=False),
        Arg("output_format", description="Output format (table, json, cyclonedx, cyclonedx-json, sarif)", type=str, required=False, default="table"),
        Arg("scope", description="The scope to scan (squashed, all-layers)", type=str, required=False, default="squashed"),
        Arg("only_fixed", description="Only show vulnerabilities that have a fix available", type=bool, required=False, default=False),
        Arg("platform", description="Platform to use for the container image (e.g., linux/amd64)", type=str, required=False),
        # Output control flags
        Arg("quiet", description="Show only the final summary and recommendations", type=bool, required=False, default=False),
        Arg("show_details", description="Show detailed vulnerability information", type=bool, required=False, default=True),
        Arg("show_recommendations", description="Show recommendations for fixing issues", type=bool, required=False, default=True),
    ]

    content = """
# Function to analyze vulnerabilities and provide recommendations
analyze_vulnerabilities() {
    local scan_output="$1"
    local severity_counts=""
    local has_vulnerabilities=false
    
    [ "$quiet" != "true" ] && echo "🔍 Analyzing scan results..."
    
    # Count vulnerabilities by severity
    if [ "$output_format" = "json" ]; then
        # Parse JSON output
        severity_counts=$(echo "$scan_output" | jq -r '
            [.matches[] | .vulnerability.severity | ascii_upcase] |
            reduce .[] as $sev (
                {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NEGLIGIBLE": 0};
                .[$sev] += 1
            ) | to_entries | map(select(.value > 0)) | .[] |
            "\\(.key): \\(.value)"
        ' 2>/dev/null || echo "")
        
        if [ -n "$severity_counts" ]; then
            has_vulnerabilities=true
        fi
    else
        severity_counts=$(echo "$scan_output" | grep -E "Critical|High|Medium|Low|Negligible" | sort | uniq -c | awk '{print $2": "$1}')
        if [ -n "$severity_counts" ]; then
            has_vulnerabilities=true
        fi
    fi
    
    # Print summary and recommendations
    if [ "$has_vulnerabilities" = true ]; then
        echo "
📊 Vulnerability Summary
══════════════════════"
        # Format severity counts with icons
        echo "$severity_counts" | while read -r line; do
            case "$line" in
                *"CRITICAL"*) echo "🔴 $line";;
                *"HIGH"*) echo "🟠 $line";;
                *"MEDIUM"*) echo "🟡 $line";;
                *"LOW"*) echo "🟢 $line";;
                *"NEGLIGIBLE"*) echo "⚪ $line";;
                *) echo "   $line";;
            esac
        done
        
        if [ "$show_details" = "true" ] && [ "$output_format" = "json" ]; then
            # Extract fixable vulnerabilities
            fixable=$(echo "$scan_output" | jq -r '
                [.matches[] | select(.vulnerability.fix.state == "fixed")] |
                group_by(.artifact.name) |
                map({
                    package: .[0].artifact.name,
                    version: .[0].artifact.version,
                    fixes: [.[].vulnerability.fix.versions[0]] | unique
                }) | .[] |
                "• \\(.package) (\\(.version)) → \\(.fixes | join(", "))"
            ' 2>/dev/null)
            
            if [ -n "$fixable" ]; then
                echo "
🔧 Available Fixes
═══════════════"
                echo "$fixable"
            fi
            
            # Extract critical packages
            critical_pkgs=$(echo "$scan_output" | jq -r '
                [.matches[] | select(.vulnerability.severity == "Critical")] |
                map(.artifact.name) | unique | .[]
            ' 2>/dev/null)
            
            if [ -n "$critical_pkgs" ]; then
                echo "
⚠️  Critical Packages
══════════════════"
                echo "$critical_pkgs" | while read pkg; do
                    echo "• $pkg"
                done
            fi
        fi
        
        if [ "$show_recommendations" = "true" ]; then
            echo "
💡 Recommendations
═══════════════"
            if [ "$output_format" = "json" ]; then
                echo "Most affected packages:"
                echo "$scan_output" | jq -r '
                    [.matches[] | .artifact.name] |
                    reduce .[] as $pkg ({}; .[$pkg] += 1) |
                    to_entries |
                    sort_by(.value) |
                    reverse |
                    .[0:3] |
                    .[] |
                    "• \\(.key) (\\(.value) vulnerabilities)"
                ' 2>/dev/null
            fi
            
            echo "
Action items:
1. 📦 Update packages with available fixes
2. 🛡️  Review security policies
3. 🏗️  Consider using minimal base images
4. 🔄 Implement regular security scans"
        fi
    else
        echo "✅ No vulnerabilities found!"
    fi
}

# Function to format JSON output
format_json_output() {
    if [ "$output_format" = "json" ]; then
        if [ "$show_details" = "true" ]; then
            jq '.' || {
                echo "❌ Failed to format JSON output"
                exit 1
            }
        else
            jq '{
                summary: {
                    total_vulnerabilities: (.matches | length),
                    by_severity: [.matches[] | .vulnerability.severity] | reduce .[] as $sev ({}; .[$sev] += 1)
                },
                critical_packages: [.matches[] | select(.vulnerability.severity == "Critical") | .artifact.name] | unique
            }' || {
                echo "❌ Failed to format JSON output"
                exit 1
            }
        fi
    else
        cat
    fi
}

# Function to execute Grype scan
execute_scan() {
    local cmd="$1"
    [ "$quiet" != "true" ] && echo "🚀 Executing scan: $cmd"
    [ "$quiet" != "true" ] && echo "⏳ This may take a few minutes depending on the scan scope..."
    
    # Create a temporary file for output
    local tmp_output=$(mktemp)
    
    # Execute the scan and capture output
    if ! eval "$cmd" > "$tmp_output" 2>&1; then
        local exit_code=$?
        if [ "$fail_on" != "" ] && [ $exit_code -eq 1 ]; then
            [ "$quiet" != "true" ] && echo "⚠️  Scan completed: Found vulnerabilities at or above specified severity level: $fail_on"
            [ "$show_details" = "true" ] && cat "$tmp_output" | format_json_output
            analyze_vulnerabilities "$(cat $tmp_output)"
            rm -f "$tmp_output"
            exit 1
        else
            echo "❌ Scan failed with error:"
            cat "$tmp_output"
            rm -f "$tmp_output"
            exit $exit_code
        fi
    fi
    
    # Process and display output
    [ "$quiet" != "true" ] && echo "✅ Scan completed successfully!"
    [ "$show_details" = "true" ] && cat "$tmp_output" | format_json_output
    analyze_vulnerabilities "$(cat $tmp_output)"
    rm -f "$tmp_output"
}

# Build the command
cmd="grype"

# Add the image
cmd="$cmd $image"

# Add optional arguments
if [ -n "$fail_on" ]; then
    cmd="$cmd --fail-on $fail_on"
fi

if [ -n "$output_format" ]; then
    cmd="$cmd -o $output_format"
fi

if [ -n "$scope" ]; then
    cmd="$cmd -s $scope"
fi

if [ "$only_fixed" = "true" ]; then
    cmd="$cmd --only-fixed"
fi

if [ -n "$platform" ]; then
    cmd="$cmd --platform $platform"
fi

# Execute the scan
execute_scan "$cmd"
"""

    return GrypeTool(
        name="scan_image_tool",
        description="Scan a container image for vulnerabilities using Grype",
        content=content,
        args=args,
        long_running=True
    )

def create_scan_directory_tool():
    args = [
        Arg("directory", description="The directory to scan", type=str),
        Arg("fail_on", description="Exit with error code if vulnerability found with severity >= specified level (negligible, low, medium, high, critical)", type=str, required=False),
        Arg("output_format", description="Output format (table, json, cyclonedx, cyclonedx-json, sarif)", type=str, required=False, default="table"),
        Arg("only_fixed", description="Only show vulnerabilities that have a fix available", type=bool, required=False, default=False),
    ]

    content = """
# Function to analyze vulnerabilities and provide recommendations
analyze_vulnerabilities() {
    local scan_output="$1"
    local severity_counts=""
    local has_vulnerabilities=false
    
    echo "\\nAnalyzing scan results..."
    
    # Count vulnerabilities by severity
    if [ "$output_format" = "json" ]; then
        # Parse JSON output
        severity_counts=$(echo "$scan_output" | jq -r '
            [.matches[] | .vulnerability.severity | ascii_upcase] |
            reduce .[] as $sev (
                {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NEGLIGIBLE": 0};
                .[$sev] += 1
            ) | to_entries | map(select(.value > 0)) | .[] |
            "\\(.key): \\(.value)"
        ' 2>/dev/null || echo "")
        
        if [ -n "$severity_counts" ]; then
            has_vulnerabilities=true
        fi
    else
        severity_counts=$(echo "$scan_output" | grep -E "Critical|High|Medium|Low|Negligible" | sort | uniq -c | awk '{print $2": "$1}')
        if [ -n "$severity_counts" ]; then
            has_vulnerabilities=true
        fi
    fi
    
    # Print summary and recommendations
    if [ "$has_vulnerabilities" = true ]; then
        echo "\\nVulnerability Summary:"
        echo "$severity_counts"
        
        echo "\\nRecommendations:"
        if [ "$output_format" = "json" ]; then
            # Extract fixable vulnerabilities
            fixable=$(echo "$scan_output" | jq -r '
                [.matches[] | select(.vulnerability.fix.state == "fixed")] |
                group_by(.artifact.name) |
                map({
                    package: .[0].artifact.name,
                    version: .[0].artifact.version,
                    fixes: [.[].vulnerability.fix.versions[0]] | unique
                }) | .[] |
                "- Update \\(.package) from \\(.version) to one of: \\(.fixes | join(", "))"
            ' 2>/dev/null)
            
            if [ -n "$fixable" ]; then
                echo "Available fixes:"
                echo "$fixable"
            fi
            
            # Extract critical packages
            critical_pkgs=$(echo "$scan_output" | jq -r '
                [.matches[] | select(.vulnerability.severity == "Critical")] |
                map(.artifact.name) | unique | .[]
            ' 2>/dev/null)
            
            if [ -n "$critical_pkgs" ]; then
                echo "\\nCritical packages to review:"
                echo "$critical_pkgs" | while read pkg; do
                    echo "- $pkg"
                done
            fi
        fi
        
        # Directory-specific recommendations
        echo "\\nDirectory-specific recommendations:"
        echo "1. Review and update package dependencies"
        echo "2. Consider implementing dependency version constraints"
        echo "3. Regularly audit dependencies for security updates"
        echo "4. Implement automated dependency updates"
    else
        echo "No vulnerabilities found! 🎉"
    fi
}

# Function to format JSON output
format_json_output() {
    if [ "$output_format" = "json" ]; then
        jq '.' || {
            echo "Failed to format JSON output"
            exit 1
        }
    else
        cat
    fi
}

# Function to execute Grype scan
execute_scan() {
    local cmd="$1"
    echo "Executing scan: $cmd"
    echo "Scanning directory contents..."
    
    # Create a temporary file for output
    local tmp_output=$(mktemp)
    
    # Execute the scan and capture output
    if ! eval "$cmd" > "$tmp_output" 2>&1; then
        local exit_code=$?
        if [ "$fail_on" != "" ] && [ $exit_code -eq 1 ]; then
            echo "Scan completed: Found vulnerabilities at or above specified severity level: $fail_on"
            cat "$tmp_output" | format_json_output
            analyze_vulnerabilities "$(cat $tmp_output)"
            rm -f "$tmp_output"
            exit 1
        else
            echo "Scan failed with error:"
            cat "$tmp_output"
            rm -f "$tmp_output"
            exit $exit_code
        fi
    fi
    
    # Process and display output
    echo "\\nScan completed successfully!"
    cat "$tmp_output" | format_json_output
    analyze_vulnerabilities "$(cat $tmp_output)"
    rm -f "$tmp_output"
}

# Verify directory exists
if [ ! -d "$directory" ]; then
    echo "Directory does not exist: $directory"
    exit 1
fi

# Build the command
cmd="grype dir:$directory"

# Add optional arguments
if [ -n "$fail_on" ]; then
    cmd="$cmd --fail-on $fail_on"
fi

if [ -n "$output_format" ]; then
    cmd="$cmd -o $output_format"
fi

if [ "$only_fixed" = "true" ]; then
    cmd="$cmd --only-fixed"
fi

# Execute the scan
execute_scan "$cmd"
"""

    return GrypeTool(
        name="scan_directory",
        description="Scan a directory for vulnerabilities using Grype",
        content=content,
        args=args,
        long_running=True
    )

def create_scan_sbom_tool():
    args = [
        Arg("sbom_file", description="Path to the SBOM file (supports Syft JSON, SPDX, CycloneDX)", type=str),
        Arg("fail_on", description="Exit with error code if vulnerability found with severity >= specified level (negligible, low, medium, high, critical)", type=str, required=False),
        Arg("output_format", description="Output format (table, json, cyclonedx, cyclonedx-json, sarif)", type=str, required=False, default="table"),
        Arg("only_fixed", description="Only show vulnerabilities that have a fix available", type=bool, required=False, default=False),
        Arg("add_cpes_if_none", description="Add CPEs if none are found in the SBOM", type=bool, required=False, default=False),
    ]

    content = """
# Function to analyze vulnerabilities and provide recommendations
analyze_vulnerabilities() {
    local scan_output="$1"
    local severity_counts=""
    local has_vulnerabilities=false
    
    echo "\\nAnalyzing scan results..."
    
    # Count vulnerabilities by severity
    if [ "$output_format" = "json" ]; then
        # Parse JSON output
        severity_counts=$(echo "$scan_output" | jq -r '
            [.matches[] | .vulnerability.severity | ascii_upcase] |
            reduce .[] as $sev (
                {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NEGLIGIBLE": 0};
                .[$sev] += 1
            ) | to_entries | map(select(.value > 0)) | .[] |
            "\\(.key): \\(.value)"
        ' 2>/dev/null || echo "")
        
        if [ -n "$severity_counts" ]; then
            has_vulnerabilities=true
        fi
    else
        severity_counts=$(echo "$scan_output" | grep -E "Critical|High|Medium|Low|Negligible" | sort | uniq -c | awk '{print $2": "$1}')
        if [ -n "$severity_counts" ]; then
            has_vulnerabilities=true
        fi
    fi
    
    # Print summary and recommendations
    if [ "$has_vulnerabilities" = true ]; then
        echo "\\nVulnerability Summary:"
        echo "$severity_counts"
        
        echo "\\nRecommendations:"
        if [ "$output_format" = "json" ]; then
            # Extract fixable vulnerabilities
            fixable=$(echo "$scan_output" | jq -r '
                [.matches[] | select(.vulnerability.fix.state == "fixed")] |
                group_by(.artifact.name) |
                map({
                    package: .[0].artifact.name,
                    version: .[0].artifact.version,
                    fixes: [.[].vulnerability.fix.versions[0]] | unique
                }) | .[] |
                "- Update \\(.package) from \\(.version) to one of: \\(.fixes | join(", "))"
            ' 2>/dev/null)
            
            if [ -n "$fixable" ]; then
                echo "Available fixes:"
                echo "$fixable"
            fi
            
            # Extract critical packages
            critical_pkgs=$(echo "$scan_output" | jq -r '
                [.matches[] | select(.vulnerability.severity == "Critical")] |
                map(.artifact.name) | unique | .[]
            ' 2>/dev/null)
            
            if [ -n "$critical_pkgs" ]; then
                echo "\\nCritical packages to review:"
                echo "$critical_pkgs" | while read pkg; do
                    echo "- $pkg"
                done
            fi
        fi
        
        # SBOM-specific recommendations
        echo "\\nSBOM-specific recommendations:"
        echo "1. Keep SBOM up to date with current dependencies"
        echo "2. Consider implementing automated SBOM generation"
        echo "3. Include SBOM analysis in CI/CD pipeline"
        echo "4. Use SBOM for compliance and audit purposes"
    else
        echo "No vulnerabilities found! 🎉"
    fi
}

# Function to format JSON output
format_json_output() {
    if [ "$output_format" = "json" ]; then
        jq '.' || {
            echo "Failed to format JSON output"
            exit 1
        }
    else
        cat
    fi
}

# Function to execute Grype scan
execute_scan() {
    local cmd="$1"
    echo "Executing scan: $cmd"
    echo "Analyzing SBOM file..."
    
    # Create a temporary file for output
    local tmp_output=$(mktemp)
    
    # Execute the scan and capture output
    if ! eval "$cmd" > "$tmp_output" 2>&1; then
        local exit_code=$?
        if [ "$fail_on" != "" ] && [ $exit_code -eq 1 ]; then
            echo "Scan completed: Found vulnerabilities at or above specified severity level: $fail_on"
            cat "$tmp_output" | format_json_output
            analyze_vulnerabilities "$(cat $tmp_output)"
            rm -f "$tmp_output"
            exit 1
        else
            echo "Scan failed with error:"
            cat "$tmp_output"
            rm -f "$tmp_output"
            exit $exit_code
        fi
    fi
    
    # Process and display output
    echo "\\nScan completed successfully!"
    cat "$tmp_output" | format_json_output
    analyze_vulnerabilities "$(cat $tmp_output)"
    rm -f "$tmp_output"
}

# Verify SBOM file exists
if [ ! -f "$sbom_file" ]; then
    echo "SBOM file does not exist: $sbom_file"
    exit 1
fi

# Build the command
cmd="grype sbom:$sbom_file"

# Add optional arguments
if [ -n "$fail_on" ]; then
    cmd="$cmd --fail-on $fail_on"
fi

if [ -n "$output_format" ]; then
    cmd="$cmd -o $output_format"
fi

if [ "$only_fixed" = "true" ]; then
    cmd="$cmd --only-fixed"
fi

if [ "$add_cpes_if_none" = "true" ]; then
    cmd="$cmd --add-cpes-if-none"
fi

# Execute the scan
execute_scan "$cmd"
"""

    return GrypeTool(
        name="scan_sbom",
        description="Scan an SBOM file for vulnerabilities using Grype",
        content=content,
        args=args,
        long_running=True
    ) 