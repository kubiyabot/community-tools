import sys
import requests
from datetime import datetime
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Search access requests with various filters')
    parser.add_argument('status', nargs='?', help='Filter by status (pending/approved/rejected)')
    parser.add_argument('tool_name', nargs='?', help='Filter by tool name')
    parser.add_argument('--user_email', help='Filter by user email')
    parser.add_argument('--group', help='Filter by group name')
    parser.add_argument('--created_after', help='Filter requests created after date (YYYY-MM-DD)')
    parser.add_argument('--created_before', help='Filter requests created before date (YYYY-MM-DD)')
    return parser.parse_args()

def filter_requests(requests, args):
    filtered = requests

    if args.status:
        status_map = {
            'pending': False,
            'approved': True,
        }
        if args.status.lower() in status_map:
            filtered = [
                req for req in filtered 
                if req.get('approved') == status_map[args.status.lower()]
            ]

    if args.tool_name:
        filtered = [
            req for req in filtered 
            if args.tool_name.lower() in req.get('request', {}).get('tool', {}).get('name', '').lower()
        ]

    if args.user_email:
        filtered = [
            req for req in filtered 
            if req.get('request', {}).get('user', {}).get('email', '').lower() == args.user_email.lower()
        ]

    if args.group:
        filtered = [
            req for req in filtered 
            if any(
                group.get('name', '').lower() == args.group.lower() 
                for group in req.get('request', {}).get('user', {}).get('groups', [])
            )
        ]

    if args.created_after:
        try:
            date_after = datetime.strptime(args.created_after, '%Y-%m-%d')
            filtered = [
                req for req in filtered 
                if datetime.strptime(req.get('created_at', '').split('T')[0], '%Y-%m-%d') >= date_after
            ]
        except ValueError:
            print(f"Warning: Invalid created_after date format. Expected YYYY-MM-DD")

    if args.created_before:
        try:
            date_before = datetime.strptime(args.created_before, '%Y-%m-%d')
            filtered = [
                req for req in filtered 
                if datetime.strptime(req.get('created_at', '').split('T')[0], '%Y-%m-%d') <= date_before
            ]
        except ValueError:
            print(f"Warning: Invalid created_before date format. Expected YYYY-MM-DD")

    return filtered

def format_request(req):
    return {
        'id': req.get('id'),
        'status': 'approved' if req.get('approved') else 'pending',
        'tool_name': req.get('request', {}).get('tool', {}).get('name'),
        'user_email': req.get('request', {}).get('user', {}).get('email'),
        'created_at': req.get('created_at'),
        'ttl': req.get('ttl'),
        'groups': [g.get('name') for g in req.get('request', {}).get('user', {}).get('groups', [])]
    }

def main():
    args = parse_arguments()
    
    try:
        res = requests.get("http://enforcer.kubiya:5001/requests/list")
        res.raise_for_status()
        
        all_requests = res.json()
        if not all_requests:
            print("No requests found.")
            return
        
        filtered_requests = filter_requests(all_requests, args)
        
        if not filtered_requests:
            print("No matching requests found.")
            return
        
        # Format and print results
        for req in filtered_requests:
            formatted = format_request(req)
            print("\n---")
            print(f"ID: {formatted['id']}")
            print(f"Status: {formatted['status']}")
            print(f"Tool: {formatted['tool_name']}")
            print(f"User: {formatted['user_email']}")
            print(f"Created: {formatted['created_at']}")
            print(f"TTL: {formatted['ttl']}")
            print(f"Groups: {', '.join(formatted['groups'])}")
            
    except requests.RequestException as e:
        print(f"Failed to fetch requests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()