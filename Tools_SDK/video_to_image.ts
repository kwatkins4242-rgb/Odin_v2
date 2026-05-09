


import { alibaba, type AlibabaVideoModelOptions } from '@ai-sdk/alibaba';
import { experimental_generateVideo as generateVideo } from 'ai';

const { video } = await generateVideo({
    model: alibaba.video('wan2.6-i2v'),
    prompt: {
        image: 'https://example.com/landscape.jpg',
        text: 'Camera slowly pans across the landscape',
    },
    duration: 5,
    providerOptions: {
        alibaba: {
            pollTimeoutMs: 600000, // 10 minutes
        } satisfies AlibabaVideoModelOptions,
    },
});






