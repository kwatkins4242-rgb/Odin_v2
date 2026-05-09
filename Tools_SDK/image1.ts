




import { groq } from '@ai-sdk/groq';
import { generateText } from 'ai';
import { readFileSync } from 'fs';

const imageData = readFileSync('path/to/image.jpg', 'base64');

const { text } = await generateText({
    model: groq('meta-llama/llama-4-scout-17b-16e-instruct'),
    messages: [
        {
            role: 'user',
            content: [
                { type: 'text', text: 'Describe this image in detail.' },
                {
                    type: 'image',
                    image: `data:image/jpeg;base64,${imageData}`,
                },
            ],
        },
    ],
});

