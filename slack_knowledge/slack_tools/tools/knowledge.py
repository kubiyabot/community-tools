def slack_knowledge():
    try:
        import os
        import json
        import litellm
        import requests

        from pydantic import BaseModel
        from slack_sdk import WebClient

        client = WebClient(token=os.environ["SLACK_API_TOKEN"])

        class SlackMessage(BaseModel):
            ts: str
            user: str
            text: str
            thread_ts: str | None = None
            channel_id: str

        class SlackMessageKnowledgeMD(BaseModel):
            ts: str
            user: str
            channel_id: str
            thread_ts: str | None = None

        class SlackThreadedMessageKnowledge(BaseModel):
            content: str
            metadata: SlackMessageKnowledgeMD

        class SlackMessageKnowledge(BaseModel):
            content: str
            metadata: SlackMessageKnowledgeMD
            relevance: float
            thread: list[SlackThreadedMessageKnowledge]

        class ThreadResponse(BaseModel):
            answer: str | None = None
            question: str | None = None

        class AnswerReference(BaseModel):
            ts: str
            channel_id: str

        class Answer(BaseModel):
            content: str
            references: list[AnswerReference]

        def get_thread_messages(channel_id: str, ts: str) -> list[SlackMessage]:
            response = client.conversations_replies(ts=ts, channel=channel_id, limit=100)

            return [SlackMessage(**m, channel_id=channel_id) for m in response["messages"]]

        def remove_kubi_messages(
            messages: list[SlackMessageKnowledge],
            bot_user_id: str,
        ) -> list[SlackMessageKnowledge]:
            filtered_messages = []
            for msg in messages:
                # Filter out kubi messages from the thread
                filtered_thread = []
                for thread_msg in msg.thread:
                    if thread_msg.metadata.user != bot_user_id:
                        filtered_thread.append(thread_msg)

                # Create a new SlackMessageKnowledge with filtered thread
                filtered_msg = SlackMessageKnowledge(
                    content=msg.content,
                    metadata=msg.metadata,
                    relevance=msg.relevance,
                    thread=filtered_thread,
                )
                filtered_messages.append(filtered_msg)

            return filtered_messages

        def format_slack_thread(messages: list[SlackMessage]):
            formatted = "Message Thread:\n"
            for msg in messages:
                formatted_msg = f"User: {msg.user} Text: {msg.text}\n"

                formatted += formatted_msg

            return formatted

        def format_slack_threads(messages: list[SlackMessageKnowledge]):
            formatted = []
            for msg in messages:
                main_content = msg.content.strip()
                metadata = msg.metadata
                channel_id = metadata.channel_id
                ts = metadata.ts

                formatted_msg = (
                    f"Main Message (relevance score: {msg.relevance}):\n"
                    f"{main_content}\n"
                    f"(channel_id: {channel_id}, ts: {ts})"
                )

                thread_replies = msg.thread
                if thread_replies:
                    formatted_msg += "\n\nThread Replies:"
                    for reply in thread_replies:
                        reply_content = reply.content.strip()
                        reply_channel_id = reply.metadata.channel_id
                        reply_ts = reply.metadata.ts
                        formatted_msg += (
                            f"\n  - {reply_content} "
                            f"(Channel ID: {reply_channel_id}, Timestamp: {reply_ts})"
                        )

                formatted.append(formatted_msg)

            return "\n\n---\n\n".join(formatted)

        def query_rag(query: str, channel_id: str) -> list[SlackMessageKnowledge]:
            kubiya_api_url = os.environ.get("KUBIYA_API_URL", "https://api.kubiya.ai")
            payload = {
                "threshold": 0.55,
                "query": query,
                "channel_id": channel_id,
            }
            headers = {
                "Authorization": f"UserKey {os.environ['KUBIYA_API_KEY']}",
            }
            result = requests.post(
                f"{kubiya_api_url}/api/v1/rag/query/slack", json=payload, headers=headers
            )
            result.raise_for_status()

            return [SlackMessageKnowledge(**msg) for msg in result.json()]

        def pretty_print_answer(answer: Answer):
            slack_domain = os.environ["SLACK_DOMAIN"]
            print(f"Answer: {answer.content}")
            print("\n  References:")
            for ref in answer.references:
                print(
                    f" - https://{slack_domain}.slack.com/archives/{ref.channel_id}/p{ref.ts}"
                )

        def _get_bot_user_id() -> str:
            user_id = client.auth_test().get("user_id")
            if not user_id:
                raise ValueError("Bot user ID not found")
            return user_id

        llm_key = os.environ["LLM_API_KEY"]
        llm_base_url = os.environ["LLM_BASE_URL"]

        thread_messages = get_thread_messages(
            os.environ["SLACK_CHANNEL_ID"], os.environ["SLACK_THREAD_TS"]
        )
        thread_context = format_slack_thread(thread_messages)
        response = litellm.completion(
            model="openai/gpt-4o",
            api_key=llm_key,
            base_url=llm_base_url,
            response_format=ThreadResponse,
            extra_body={
                "metadata": {
                    "kubiya_org": os.environ["KUBIYA_USER_ORG"],
                    "trace_user_id": f"{os.environ['KUBIYA_USER_EMAIL']}-{os.environ['KUBIYA_USER_ORG']}",
                    "kubiya_user_email": os.environ["KUBIYA_USER_EMAIL"],
                    "trace_name": "slack-knowledge",
                    "generation_name": "slack-knowledge-thread-extraction",
                }
            },
            messages=[
                {
                    "content": """
Extract the most relevant user question from the thread to search a knowledge base.
	•	If the users latest message is a question, return it.
	•	If not, return the most recent user question from the thread.
	•	If the thread already contains an answer to that question, return the answer instead.
""",
                    "role": "system",
                },
                {
                    "content": f"Thread context: {thread_context}\n\nUser message: {os.environ['KUBIYA_USER_MESSAGE']}",
                    "role": "user",
                },
            ],
        )

        thread_res = ThreadResponse(**json.loads(response.choices[0].message.content))

        if thread_res.answer:
            print(f"Answer (based on the thread): {thread_res.answer}")
            return

        if not thread_res.question:
            print("Question could not be extracted from the thread")
            return

        result = query_rag(thread_res.question, os.environ["SLACK_CHANNEL_ID"])

        if not result:
            print("No relevant information found in the knowledge base")
            return

        result = remove_kubi_messages(result, _get_bot_user_id())
        has_thread = False
        for msg in result:
            if len(msg.thread) > 0:
                has_thread = True

        if has_thread is False:
            print("No thread messages found for relevant answers")
            return

        formated_result = format_slack_threads(result)

        response = litellm.completion(
            model="openai/gpt-4o",
            api_key=llm_key,
            base_url=llm_base_url,
            response_format=Answer,
            extra_body={
                "metadata": {
                    "kubiya_org": os.environ["KUBIYA_USER_ORG"],
                    "trace_user_id": f"{os.environ['KUBIYA_USER_EMAIL']}-{os.environ['KUBIYA_USER_ORG']}",
                    "kubiya_user_email": os.environ["KUBIYA_USER_EMAIL"],
                    "trace_name": "slack-knowledge",
                    "generation_name": "slack-knowledge-answer",
                }
            },
            messages=[
                {
                    "content": """
You are a helpful assistant that can answer questions based on the provided knowledge base ONLY. You are given a query and a result from a knowledge base. You need to answer the query based on the result.
Keep your response concise and to the point. Answer and cite answers from the knowledge base BUT make sure they are in an answer format.
    """,
                    "role": "system",
                },
                {
                    "content": f"question: {thread_res.question}\n\v knowledge base:\n{formated_result}",
                    "role": "user",
                },
            ],
        )
        answer = Answer(**json.loads(response.choices[0].message.content))

        pretty_print_answer(answer)

    except Exception as e:
        print(e)
        print("tool ended with error")
        exit(1)


if __name__ == "__main__":
    slack_knowledge()
