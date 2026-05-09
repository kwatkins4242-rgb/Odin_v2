


import { alibaba, type AlibabaVideoModelOptions } from '@ai-sdk/alibaba';
import { experimental_generateVideo as generateVideo } from 'ai';

const { video } = await generateVideo({
    model: alibaba.video('wan2.6-r2v-flash'),
    prompt: 'character1 walks through a beautiful garden and waves at the camera',
    resolution: '1280x720',
    duration: 5,
    providerOptions: {
        alibaba: {
            referenceUrls: ['https://example.com/character-reference.jpg'],
            pollTimeoutMs: 600000, // 10 minutes
        } satisfies AlibabaVideoModelOptions,
    },
});

