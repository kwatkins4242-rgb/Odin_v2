

import { cencori } from 'cencori/vercel';
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: cencori('gemini-2.5-flash'),
    messages,
  });

  return result.toDataStreamResponse();
