

import { alibaba } from '@ai-sdk/alibaba';
import { generateText } from 'ai';

const longDocument = '... large document content ...';

const { text, usage } = await generateText({
    model: alibaba('qwen-plus'),
    messages: [
        {
            role: 'user',
            content: [
                {
                    type: 'text',
                    text: 'Context: Please analyze this document.',
                },
                {
                    type: 'text',
                    text: longDocument,
                    providerOptions: {
                        alibaba: {
                            cacheControl: { type: 'ephemeral' },
                        },
                    },
                },
            ],
        },
    ],
});

