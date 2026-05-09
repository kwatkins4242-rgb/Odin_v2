import {
    moonshotai,
    type MoonshotAILanguageModelOptions,
} from '@ai-sdk/moonshotai';
import { generateText } from 'ai';

const { text, reasoningText } = await generateText({
    model: moonshotai('kimi-k2-thinking'),
    providerOptions: {
        moonshotai: {
            thinking: { type: 'enabled', budgetTokens: 2048 },
            reasoningHistory: 'interleaved',
        } satisfies MoonshotAILanguageModelOptions,
    },
    prompt: 'How many "r"s are in the word "strawberry"?',
});

console.log(reasoningText);
console.log(text);