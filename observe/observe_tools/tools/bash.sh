# Validate authentication
if [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$OBSERVE_API_KEY" ]; then
    echo "Error: OBSERVE_CUSTOMER_ID and OBSERVE_API_KEY environment variables are required"
    exit 1
fi

# Validate required parameters
if [ -z "$alert_id" ]; then
    echo "Error: alert_id is required"
    exit 1
fi

echo "Fetching alert details from Observe..."
echo "Alert ID: $alert_id"

# Call Observe API to get alert details
RESPONSE=$(curl -s -X GET "https://api.observeinc.com/v1/customers/$OBSERVE_CUSTOMER_ID/alerts/$alert_id" \
    -H "Authorization: Bearer $OBSERVE_API_KEY" \
    -H "Content-Type: application/json")

# Print alert details
echo "============================================="
echo "ALERT DETAILS"
echo "============================================="

# Extract relevant fields and format them
echo "$RESPONSE" | jq -r '
    "ID: \(.id // "N/A")",
    "Name: \(.name // "N/A")",
    "Status: \(.status // "N/A")",
    "Severity: \(.severity // "N/A")",
    "Created: \(.created_at // "N/A")",
    "Updated: \(.updated_at // "N/A")",
    "Description: \(.description // "N/A")",
    "----------------------",
    "Monitor ID: \(.monitor_id // "N/A")",
    "Dataset ID: \(.dataset_id // "N/A")",
    "----------------------",
    "Associated Resources:",
    (.resources // [] | map("- \(.)") | join("\n")),
    "----------------------",
    "Alert URL: https://app.observeinc.com/alerts/\(.id // "N/A")"
'

# If the alert has a monitor, fetch monitor details
MONITOR_ID=$(echo "$RESPONSE" | jq -r '.monitor_id // ""')

if [ -n "$MONITOR_ID" ]; then
    echo ""
    echo "Fetching related monitor details..."
    
    # Call Observe API to get monitor details
    MONITOR_RESPONSE=$(curl -s -X GET "https://api.observeinc.com/v1/customers/$OBSERVE_CUSTOMER_ID/monitors/$MONITOR_ID" \
        -H "Authorization: Bearer $OBSERVE_API_KEY" \
        -H "Content-Type: application/json")
    
    if ! echo "$MONITOR_RESPONSE" | jq -e '.error' > /dev/null; then
        echo "============================================="
        echo "MONITOR DETAILS"
        echo "============================================="
        
        echo "$MONITOR_RESPONSE" | jq -r '
            "ID: \(.id // "N/A")",
            "Name: \(.name // "N/A")",
            "Type: \(.type // "N/A")",
            "Status: \(.status // "N/A")",
            "Dataset: \(.dataset_name // "N/A")",
            "Query: \(.query // "N/A")",
            "----------------------",
            "Monitor URL: https://app.observeinc.com/monitors/\(.id // "N/A")"
        '
    else
        echo "Unable to fetch monitor details."
    fi
fi

echo ""
echo "Alert information retrieval complete."