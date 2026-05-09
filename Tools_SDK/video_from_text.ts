



import { alibaba, type AlibabaVideoModelOptions } from '@ai-sdk/alibaba';
import { experimental_generateVideo as generateVideo } from 'ai';

const { video } = await generateVideo({
    model: alibaba.video('wan2.6-t2v'),
    prompt: 'A serene mountain lake at sunset with gentle ripples on the water.',
    resolution: '1280x720',
    duration: 5,
    providerOptions: {
        alibaba: {
            promptExtend: true,
            pollTimeoutMs: 600000, // 10 minutes
        } satisfies AlibabaVideoModelOptions,
    },
});
