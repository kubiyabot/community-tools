# Function to extract relevant error context from logs efficiently
function extract_error_context() {
    awk '
        BEGIN {
            # Configure sizes
            max_buffer = 100    # Lines to keep before error
            after_lines = 20    # Lines to show after error
            buffer_size = 0     # Current buffer size
            buffer_start = 0    # Start position in circular buffer
            printing = 0        # Number of lines left to print after match
            
            # Error patterns
            err_pattern = "(error|Error|ERROR|exited|Exited|failed|Failed|FAILED|exit code|Exception|EXCEPTION|fatal|Fatal|FATAL)"
            # Noise patterns to filter
            noise_pattern = "(Download|Progress|download|progress)"
        }
        
        # Skip noisy lines early
        $0 ~ noise_pattern { next }
        
        {
            # Store in circular buffer
            buffer_pos = (buffer_start + buffer_size) % max_buffer
            buffer[buffer_pos] = $0
            
            if (buffer_size < max_buffer) {
                buffer_size++
            } else {
                buffer_start = (buffer_start + 1) % max_buffer
            }
            
            # Check for errors
            if ($0 ~ err_pattern) {
                # Generate a hash of the surrounding context to avoid duplicates
                context = ""
                for (i = 0; i < 3; i++) {  # Use 3 lines for context hash
                    pos = (buffer_pos - i + max_buffer) % max_buffer
                    if (buffer[pos]) {
                        context = context buffer[pos]
                    }
                }
                context_hash = context
                
                # Only print if we have not seen this context
                if (!(context_hash in seen)) {
                    seen[context_hash] = 1
                    
                    # Print separator for readability
                    print "\\n=== Error Context ===\\n"
                    
                    # Print buffer content (previous lines)
                    for (i = 0; i < buffer_size; i++) {
                        pos = (buffer_start + i) % max_buffer
                        print buffer[pos]
                    }
                    
                    # Start printing aftermath
                    printing = after_lines
                }
            }
            else if (printing > 0) {
                print
                printing--
                if (printing == 0) {
                    print "\\n=== End of Context ===\\n"
                }
            }
        }
    '
}

# Function to search logs with context efficiently
function search_logs_with_context() {
    local pattern="$1"
    local before_context="${2:-5}"
    local after_context="${3:-5}"
    
    awk -v pattern="$pattern" -v before="$before_context" -v after="$after_context" '
        BEGIN {
            # Initialize circular buffer
            max_buffer = before + 1
            buffer_size = 0
            buffer_start = 0
            printing = 0
            
            # Noise pattern to filter
            noise_pattern = "(Download|Progress|download|progress)"
        }
        
        # Skip noisy lines early
        $0 ~ noise_pattern { next }
        
        {
            # Store in circular buffer
            buffer_pos = (buffer_start + buffer_size) % max_buffer
            buffer[buffer_pos] = $0
            
            if (buffer_size < max_buffer) {
                buffer_size++
            } else {
                buffer_start = (buffer_start + 1) % max_buffer
            }
            
            # Check for pattern match
            if ($0 ~ pattern) {
                # Generate context hash to avoid duplicates
                context_hash = $0  # Use matching line as hash
                
                if (!(context_hash in seen)) {
                    seen[context_hash] = 1
                    
                    print "\\n=== Match Found ===\\n"
                    
                    # Print previous lines from buffer
                    for (i = 0; i < buffer_size - 1; i++) {
                        pos = (buffer_start + i) % max_buffer
                        print "BEFORE | " buffer[pos]
                    }
                    
                    # Print matching line
                    print "MATCH  | " $0
                    
                    # Start printing aftermath
                    printing = after
                }
            }
            else if (printing > 0) {
                print "AFTER  | " $0
                printing--
                if (printing == 0) {
                    print "\\n=== End of Match ===\\n"
                }
            }
        }
    '
}
