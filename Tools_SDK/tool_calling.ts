

import { cencori } from 'cencori/vercel';
import { generateText, tool } from 'ai';
import { z } from 'zod';

const { text, toolCalls } = await generateText({
  model: cencori('gpt-4o'),
  prompt: 'What is the weather in San Francisco?',
  tools: {
    getWeather: tool({
      description: 'Get the weather for a location',
      parameters: z.object({
        location: z.string().describe('The city and state'),
      }),
      execute: async ({ location }) => {
        return { temperature: 72, condition: 'sunny', location };
      },
    }),
  },
});

console.log(text, toolCalls);


