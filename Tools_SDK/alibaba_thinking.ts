
Thinking mode


import { alibaba, type AlibabaLanguageModelOptions } from '@ai-sdk/alibaba';
import { generateText } from 'ai';

const { text, reasoning } = await generateText({
    model: alibaba('qwen3-max'),
    providerOptions: {
        alibaba: {
            enableThinking: true,
            thinkingBudget: 2048,
        } satisfies AlibabaLanguageModelOptions,
    },
    prompt: 'How many "r"s are in the word "strawberry"?',
});

console.log('Reasoning:', reasoning);
console.log('Answer:', text);








