import { alibaba } from '@ai-sdk/alibaba';
import { generateText } from 'ai';

const { text } = await generateText({
    model: alibaba('qwen-plus'),
    prompt: 'Write a vegetarian lasagna recipe for 4 people.',
});
Language factory
const model = alibaba.chatModel('qwen-plus');
// or
const model = alibaba.languageModel('qwen-plus');
