from typing import List
import sys
from .base import JenkinsTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class BuildAnalyzer:
    """Analyze Jenkins builds and their logs."""
    
    def __init__(self):
        """Initialize and register all tools."""
        try:
            # Create and register tools
            tools = [
                self.get_failed_build_logs(),
                self.analyze_build_failure(),
                self.get_build_artifacts(),
                self.compare_builds()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("jenkins", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise

        except Exception as e:
            print(f"❌ Failed to register Jenkins build tools: {str(e)}", file=sys.stderr)
            raise

    def get_failed_build_logs(self) -> JenkinsTool:
        """Get logs from a failed build."""
        return JenkinsTool(
            name="jenkins_build_logs_failed",
            description="Get logs from a failed build",
            content="""
            # Install jq if not present
            if ! command -v jq &> /dev/null; then
                apk add --no-cache jq
            fi

            if [ -z "$job_name" ] || [ -z "$build_number" ]; then
                echo "Error: Job name and build number are required"
                exit 1
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            # Get build URL
            BUILD_URL=$(get_build_url "$job_name" "$build_number")

            # Get build status
            STATUS=$(get_build_status "$job_name" "$build_number")
            
            echo "=== Build Information ==="
            echo "Job: $job_name"
            echo "Build: #$build_number"
            echo "Status: $STATUS"
            echo "URL: $BUILD_URL"

            # Get build logs
            echo "\n=== Build Logs ==="
            curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText"

            # Get error patterns if specified
            if [ "$analyze_errors" = "true" ]; then
                echo "\n=== Error Analysis ==="
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText" | grep -i "error\\|exception\\|failed\\|failure" || true
            fi

            # Get test results if available
            if [ "$include_tests" = "true" ]; then
                echo "\n=== Test Results ==="
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/testReport/api/json" 2>/dev/null | \
                    jq -r '.failCount, .passCount, .skipCount' || echo "No test results available"
            fi
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg(name="build_number",
                    description="Build number to analyze",
                    required=True),
                Arg(name="analyze_errors",
                    description="Analyze and highlight errors in the log",
                    required=False),
                Arg(name="include_tests",
                    description="Include test results in the output",
                    required=False)
            ],
            image="curlimages/curl:8.1.2",
        )

    def analyze_build_failure(self) -> JenkinsTool:
        """Analyze the cause of a build failure."""
        return JenkinsTool(
            name="analyze_build_failure",
            description="Analyze the cause of a build failure",
            content="""
            if [ -z "$job_name" ] || [ -z "$build_number" ]; then
                echo "Error: Job name and build number are required"
                exit 1
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            BUILD_URL=$(get_build_url "$job_name" "$build_number")

            echo "=== Build Analysis ==="
            
            # Get build details
            BUILD_INFO=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/api/json")
            
            # Extract key information
            echo "Build Duration: $(echo "$BUILD_INFO" | jq -r '.duration')"
            echo "Build Result: $(echo "$BUILD_INFO" | jq -r '.result')"
            
            # Analyze changes
            echo "\n=== Changes ==="
            curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/changes" || echo "No changes found"
            
            # Get error patterns
            echo "\n=== Error Patterns ==="
            curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText" | \
                grep -i -C 5 "error\\|exception\\|failed\\|failure" || echo "No obvious error patterns found"
            
            # Check for known issues
            echo "\n=== Known Issues Check ==="
            CONSOLE_TEXT=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText")
            
            # Common patterns to check
            if echo "$CONSOLE_TEXT" | grep -q "OutOfMemoryError"; then
                echo "❌ Memory issue detected"
            fi
            if echo "$CONSOLE_TEXT" | grep -q "Connection.*refused"; then
                echo "❌ Network connectivity issue detected"
            fi
            if echo "$CONSOLE_TEXT" | grep -q "Permission denied"; then
                echo "❌ Permission issue detected"
            fi
            if echo "$CONSOLE_TEXT" | grep -q "Timeout"; then
                echo "❌ Timeout issue detected"
            fi
            
            # Get test failures if available
            echo "\n=== Test Failures ==="
            curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/testReport/api/json" 2>/dev/null | \
                jq -r '.suites[].cases[] | select(.status=="FAILED") | "Test: " + .name + "\nError: " + .errorDetails' || \
                echo "No test report available"
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg(name="build_number",
                    description="Build number to analyze",
                    required=True)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_build_artifacts(self) -> JenkinsTool:
        """Get artifacts from a build."""
        return JenkinsTool(
            name="get_build_artifacts",
            description="Get artifacts from a build",
            content="""
            if [ -z "$job_name" ] || [ -z "$build_number" ]; then
                echo "Error: Job name and build number are required"
                exit 1
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            BUILD_URL=$(get_build_url "$job_name" "$build_number")

            echo "=== Build Artifacts ==="
            
            # Get list of artifacts
            ARTIFACTS=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/api/json" | \
                jq -r '.artifacts[] | .fileName + "," + .relativePath')

            if [ -z "$ARTIFACTS" ]; then
                echo "No artifacts found for this build"
                exit 0
            fi

            # Create artifacts directory
            ARTIFACTS_DIR="${output_dir:-artifacts}"
            mkdir -p "$ARTIFACTS_DIR"

            # Download artifacts
            echo "$ARTIFACTS" | while IFS=, read -r filename path; do
                echo "Downloading $filename..."
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/artifact/$path" \
                    -o "$ARTIFACTS_DIR/$filename"
            done

            echo "\nArtifacts downloaded to $ARTIFACTS_DIR:"
            ls -lh "$ARTIFACTS_DIR"
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg(name="build_number",
                    description="Build number to get artifacts from",
                    required=True),
                Arg(name="output_dir",
                    description="Directory to save artifacts",
                    required=False)
            ],
            image="curlimages/curl:latest"
        )

    def compare_builds(self) -> JenkinsTool:
        """Compare two builds of the same job."""
        return JenkinsTool(
            name="compare_builds",
            description="Compare two builds of the same job",
            content="""
            if [ -z "$job_name" ] || [ -z "$build_number1" ] || [ -z "$build_number2" ]; then
                echo "Error: Job name and both build numbers are required"
                exit 1
            fi

            # Validate Jenkins connection
            validate_jenkins_connection

            BUILD_URL1=$(get_build_url "$job_name" "$build_number1")
            BUILD_URL2=$(get_build_url "$job_name" "$build_number2")

            echo "=== Build Comparison ==="
            echo "Comparing builds #$build_number1 and #$build_number2 of $job_name"

            # Get build information
            BUILD1_INFO=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL1/api/json")
            BUILD2_INFO=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL2/api/json")

            # Compare basic metrics
            echo "\n=== Basic Metrics ==="
            echo "Build #$build_number1:"
            echo "Result: $(echo "$BUILD1_INFO" | jq -r '.result')"
            echo "Duration: $(echo "$BUILD1_INFO" | jq -r '.duration')"
            echo "Timestamp: $(echo "$BUILD1_INFO" | jq -r '.timestamp')"

            echo "\nBuild #$build_number2:"
            echo "Result: $(echo "$BUILD2_INFO" | jq -r '.result')"
            echo "Duration: $(echo "$BUILD2_INFO" | jq -r '.duration')"
            echo "Timestamp: $(echo "$BUILD2_INFO" | jq -r '.timestamp')"

            # Compare changes
            echo "\n=== Changes Between Builds ==="
            curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL1/changes" > changes1.txt
            curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL2/changes" > changes2.txt
            diff -u changes1.txt changes2.txt || true
            rm changes1.txt changes2.txt

            # Compare test results if available
            echo "\n=== Test Results Comparison ==="
            TEST1=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL1/testReport/api/json" 2>/dev/null || echo '{"failCount":0,"passCount":0,"skipCount":0}')
            TEST2=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL2/testReport/api/json" 2>/dev/null || echo '{"failCount":0,"passCount":0,"skipCount":0}')

            echo "Build #$build_number1:"
            echo "Failed: $(echo "$TEST1" | jq -r '.failCount')"
            echo "Passed: $(echo "$TEST1" | jq -r '.passCount')"
            echo "Skipped: $(echo "$TEST1" | jq -r '.skipCount')"

            echo "\nBuild #$build_number2:"
            echo "Failed: $(echo "$TEST2" | jq -r '.failCount')"
            echo "Passed: $(echo "$TEST2" | jq -r '.passCount')"
            echo "Skipped: $(echo "$TEST2" | jq -r '.skipCount')"
            """,
            args=[
                Arg(name="job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg(name="build_number1",
                    description="First build number to compare",
                    required=True),
                Arg(name="build_number2",
                    description="Second build number to compare",
                    required=True)
            ],
            image="curlimages/curl:latest"
        ) 

# Initialize when module is imported
BuildAnalyzer() 