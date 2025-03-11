from typing import List
from .base import JenkinsTool, Arg

class BuildAnalyzer(JenkinsTool):
    """Analyze Jenkins builds and their logs."""
    
    def __init__(self):
        super().__init__(
            name="jenkins_builds",
            description="Analyze Jenkins builds and their logs",
            content="",
            args=[],
            image="jenkins/jenkins:lts-jdk11"
        )

    def get_failed_build_logs(self) -> JenkinsTool:
        """Get logs from a failed build."""
        return JenkinsTool(
            name="jenkins_build_logs_failed",
            description="Get logs from a failed build",
            content="""
            if [ -z "$JOB_NAME" ] || [ -z "$BUILD_NUMBER" ]; then
                echo "Error: Job name and build number are required"
                exit 1
            }

            # Validate Jenkins connection
            validate_jenkins_connection

            # Get build URL
            BUILD_URL=$(get_build_url "$JOB_NAME" "$BUILD_NUMBER")

            # Get build status
            STATUS=$(get_build_status "$JOB_NAME" "$BUILD_NUMBER")
            
            echo "=== Build Information ==="
            echo "Job: $JOB_NAME"
            echo "Build: #$BUILD_NUMBER"
            echo "Status: $STATUS"
            echo "URL: $BUILD_URL"

            # Get build logs
            echo "\n=== Build Logs ==="
            curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText"

            # Get error patterns if specified
            if [ "$ANALYZE_ERRORS" = "true" ]; then
                echo "\n=== Error Analysis ==="
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/consoleText" | grep -i "error\\|exception\\|failed\\|failure" || true
            fi

            # Get test results if available
            if [ "$INCLUDE_TESTS" = "true" ]; then
                echo "\n=== Test Results ==="
                curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/testReport/api/json" 2>/dev/null | \
                    jq -r '.failCount, .passCount, .skipCount' || echo "No test results available"
            fi
            """,
            args=[
                Arg("job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg("build_number",
                    description="Build number to analyze",
                    required=True),
                Arg("analyze_errors",
                    description="Analyze and highlight errors in the log",
                    required=False),
                Arg("include_tests",
                    description="Include test results in the output",
                    required=False)
            ],
            image="curlimages/curl:latest"
        )

    def analyze_build_failure(self) -> JenkinsTool:
        """Analyze the cause of a build failure."""
        return JenkinsTool(
            name="analyze_build_failure",
            description="Analyze the cause of a build failure",
            content="""
            if [ -z "$JOB_NAME" ] || [ -z "$BUILD_NUMBER" ]; then
                echo "Error: Job name and build number are required"
                exit 1
            }

            # Validate Jenkins connection
            validate_jenkins_connection

            BUILD_URL=$(get_build_url "$JOB_NAME" "$BUILD_NUMBER")

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
                Arg("job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg("build_number",
                    description="Build number to analyze",
                    required=True)
            ],
            image="curlimages/curl:latest"
        )

    def get_build_artifacts(self) -> JenkinsTool:
        """Get artifacts from a build."""
        return JenkinsTool(
            name="get_build_artifacts",
            description="Get artifacts from a build",
            content="""
            if [ -z "$JOB_NAME" ] || [ -z "$BUILD_NUMBER" ]; then
                echo "Error: Job name and build number are required"
                exit 1
            }

            # Validate Jenkins connection
            validate_jenkins_connection

            BUILD_URL=$(get_build_url "$JOB_NAME" "$BUILD_NUMBER")

            echo "=== Build Artifacts ==="
            
            # Get list of artifacts
            ARTIFACTS=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL/api/json" | \
                jq -r '.artifacts[] | .fileName + "," + .relativePath')

            if [ -z "$ARTIFACTS" ]; then
                echo "No artifacts found for this build"
                exit 0
            fi

            # Create artifacts directory
            ARTIFACTS_DIR="${OUTPUT_DIR:-artifacts}"
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
                Arg("job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg("build_number",
                    description="Build number to get artifacts from",
                    required=True),
                Arg("output_dir",
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
            if [ -z "$JOB_NAME" ] || [ -z "$BUILD_NUMBER1" ] || [ -z "$BUILD_NUMBER2" ]; then
                echo "Error: Job name and both build numbers are required"
                exit 1
            }

            # Validate Jenkins connection
            validate_jenkins_connection

            BUILD_URL1=$(get_build_url "$JOB_NAME" "$BUILD_NUMBER1")
            BUILD_URL2=$(get_build_url "$JOB_NAME" "$BUILD_NUMBER2")

            echo "=== Build Comparison ==="
            echo "Comparing builds #$BUILD_NUMBER1 and #$BUILD_NUMBER2 of $JOB_NAME"

            # Get build information
            BUILD1_INFO=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL1/api/json")
            BUILD2_INFO=$(curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$BUILD_URL2/api/json")

            # Compare basic metrics
            echo "\n=== Basic Metrics ==="
            echo "Build #$BUILD_NUMBER1:"
            echo "Result: $(echo "$BUILD1_INFO" | jq -r '.result')"
            echo "Duration: $(echo "$BUILD1_INFO" | jq -r '.duration')"
            echo "Timestamp: $(echo "$BUILD1_INFO" | jq -r '.timestamp')"

            echo "\nBuild #$BUILD_NUMBER2:"
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

            echo "Build #$BUILD_NUMBER1:"
            echo "Failed: $(echo "$TEST1" | jq -r '.failCount')"
            echo "Passed: $(echo "$TEST1" | jq -r '.passCount')"
            echo "Skipped: $(echo "$TEST1" | jq -r '.skipCount')"

            echo "\nBuild #$BUILD_NUMBER2:"
            echo "Failed: $(echo "$TEST2" | jq -r '.failCount')"
            echo "Passed: $(echo "$TEST2" | jq -r '.passCount')"
            echo "Skipped: $(echo "$TEST2" | jq -r '.skipCount')"
            """,
            args=[
                Arg("job_name",
                    description="Name of the Jenkins job",
                    required=True),
                Arg("build_number1",
                    description="First build number to compare",
                    required=True),
                Arg("build_number2",
                    description="Second build number to compare",
                    required=True)
            ],
            image="curlimages/curl:latest"
        ) 