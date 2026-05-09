
import { alibaba } from '@ai-sdk/alibaba';
import { generateText } from 'ai';

const { text, usage } = await generateText({
    model: alibaba('qwen-plus'),
    messages: [
        {
            role: 'system',
            content: 'You are a helpful assistant. [... long system prompt ...]',
            providerOptions: {
                alibaba: {
                    cacheControl: { type: 'ephemeral' },
                },
            },
        },
    ],
});






