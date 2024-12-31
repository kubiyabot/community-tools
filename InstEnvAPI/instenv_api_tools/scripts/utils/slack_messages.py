import os
import logging
import requests

class SlackMessage:
    def __init__(self, channel, thread_ts=None):
        self.channel = channel or os.getenv('SLACK_CHANNEL_ID')
        self.thread_ts = os.getenv('SLACK_THREAD_TS') or thread_ts
        self.blocks = []
        self.api_key = os.getenv('SLACK_API_TOKEN')
        self.message_ts = None  # To store the timestamp of the message

    def send_initial_message(self, blocks):
        self.blocks = blocks
        response = self.send_message()
        if response and 'ts' in response:
            self.message_ts = response['ts']
        else:
            print(f"Failed to send message. Response: {response}")

    def update_message(self):
        self.send_message(update=True)

    def send_message(self, update=False):
        if not self.api_key:
            if os.getenv('KUBIYA_DEBUG'):
                print("No SLACK_API_TOKEN set. Slack messages will not be sent.")
            return None

        payload = {
            "channel": self.channel,
            "blocks": self.blocks
        }
        if self.thread_ts:
            payload["thread_ts"] = self.thread_ts

        url = "https://slack.com/api/chat.postMessage"
        if update and self.message_ts:
            payload["ts"] = self.message_ts
            url = "https://slack.com/api/chat.update"

        response = requests.post(
            url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            },
            json=payload
        )
        if response.status_code >= 300:
            if os.getenv('KUBIYA_DEBUG'):
                print(f"Error sending Slack message: {response.status_code} - {response.text}")
            return None
        else:
            return response.json()
    
    def search_messages(self, query, channel=None, max_pages=None):
        if not query:
            return None  # Return None immediately if no query is provided

        url = "https://slack.com/api/search.messages"
        results = []
        page = 1

        while True:
            params = {
                "query": query,
                "token": self.api_key,
                "page": page
            }
            if channel:
                params["channel"] = channel

            response = requests.get(
                url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                params=params
            )
            data = response.json()

            if not data.get('ok', False):  # Check if response is not OK
                if os.getenv('KUBIYA_DEBUG'):
                    print(f"Error from Slack API: {data.get('error', 'Unknown error')}")
                return None  # Return None to indicate an error

            results.extend(data['messages']['matches'])
            page_count = data['messages']['pagination']['page_count']
            if page >= page_count or (max_pages and page >= max_pages):
                break
            page += 1

        return results

    def extract_texts(self, query, channel=None, max_pages=None):
        search_results = self.search_messages(query, channel, max_pages)
        
        if search_results is None:
            return []  # Return an empty list if there's an error in search or no results
        
        texts = [result['text'] for result in search_results if 'text' in result]
        return texts 