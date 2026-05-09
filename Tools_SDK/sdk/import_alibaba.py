
import { alibaba } from '@ai-sdk/alibaba';

Custom config
import { createAlibaba } from '@ai-sdk/alibaba';

const alibaba = createAlibaba({
  apiKey: process.env.ALIBABA_API_KEY ?? '',
});