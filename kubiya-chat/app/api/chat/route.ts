import { getKubiyaConfig } from "@/app/config";

export const maxDuration = 30;

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const POST = async (request: Request) => {
  const config = getKubiyaConfig();
  const { messages, teammate }: { messages: Message[], teammate?: string } = await request.json();

  if (!config.apiKey) {
    return new Response(JSON.stringify({ error: "Kubiya API key not configured" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Forward the request to Kubiya API
  const response = await fetch(`${config.baseUrl}/converse/${teammate || 'default'}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${config.apiKey}`,
    },
    body: JSON.stringify({ messages }),
  });

  // Return the streaming response directly
  return new Response(response.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
};
