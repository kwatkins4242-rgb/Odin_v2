

# Alibaba Provider

[Alibaba Cloud Model Studio](https://modelstudio.console.alibabacloud.com/) provides access to the Qwen model series, including advanced reasoning capabilities.

API keys can be obtained from the [Console](https://modelstudio.console.alibabacloud.com/).

## Setup

The Alibaba provider is available via the `@ai-sdk/alibaba` module. You can install it with:

<Tabs items={['pnpm', 'npm', 'yarn', 'bun']}>
  <Tab>
    <Snippet text="pnpm add @ai-sdk/alibaba" dark />
  </Tab>
  <Tab>
    <Snippet text="npm install @ai-sdk/alibaba" dark />
  </Tab>
  <Tab>
    <Snippet text="yarn add @ai-sdk/alibaba" dark />
  </Tab>
  <Tab>
    <Snippet text="bun add @ai-sdk/alibaba" dark />
  </Tab>
</Tabs>

## Provider Instance

You can import the default provider instance `alibaba` from `@ai-sdk/alibaba`:

```ts
import { alibaba } from '@ai-sdk/alibaba';
```

For custom configuration, you can import `createAlibaba` and create a provider instance with your settings:

```ts
import { createAlibaba } from '@ai-sdk/alibaba';

const alibaba = createAlibaba({
  apiKey: process.env.ALIBABA_API_KEY ?? '',
});
```




You can use the following optional settings to customize the Alibaba provider instance:

- **baseURL** _string_

  Use a different URL prefix for API calls, e.g. to use proxy servers or regional endpoints.
  The default prefix is `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`.

- **videoBaseURL** _string_

  Use a different URL prefix for video generation API calls. The video API uses the DashScope
  native endpoint (not the OpenAI-compatible endpoint).
  The default prefix is `https://dashscope-intl.aliyuncs.com`.

- **apiKey** _string_

  API key that is being sent using the `Authorization` header. It defaults to
  the `ALIBABA_API_KEY` environment variable.

- **headers** _Record&lt;string,string&gt;_

  Custom headers to include in the requests.

- **fetch** _(input: RequestInfo, init?: RequestInit) => Promise&lt;Response&gt;_

  Custom [fetch](https://developer.mozilla.org/en-US/docs/Web/API/fetch) implementation.

- **includeUsage** _boolean_

  Include usage information in streaming responses. When enabled, token usage will be included in the final chunk.
  Defaults to `true`.

## Language Models

You can create language models using a provider instance:


import { alibaba } from '@ai-sdk/alibaba';
import { generateText } from 'ai';

const { text } = await generateText({
  model: alibaba('qwen-plus'),
  prompt: 'Write a vegetarian lasagna recipe for 4 people.',
});












You can also use the `.chatModel()` or `.languageModel()` factory methods:

```ts
const model = alibaba.chatModel('qwen-plus');
// or
const model = alibaba.languageModel('qwen-plus');
```

Alibaba language models can be used in the `streamText` function
(see [AI SDK Core](/docs/ai-sdk-core)).

The following optional provider options are available for Alibaba models:

- **enableThinking** _boolean_

  Enable thinking/reasoning mode for supported models. When enabled, the model generates reasoning content before the response.
  Defaults to `false`.

- **thinkingBudget** _number_

  Maximum number of reasoning tokens to generate. Limits the length of thinking content.

- **parallelToolCalls** _boolean_

  Whether to enable parallel function calling during tool use.
  Defaults to `true`.

### Thinking Mode

Alibaba's Qwen models support thinking/reasoning mode for complex problem-solving:








### Video Provider Options

The following provider options are available via `providerOptions.alibaba`:

- **negativePrompt** _string_

  A description of what to avoid in the generated video (max 500 characters).

- **audioUrl** _string_

  URL to an audio file for audio-video sync (WAV/MP3, 3-30 seconds, max 15MB).

- **promptExtend** _boolean_

  Enable prompt extension/rewriting for better generation quality. Defaults to `true`.

- **shotType** `'single'` | `'multi'`

  Shot type for video generation. `'multi'` enables multi-shot cinematic narrative (wan2.6 models only).

- **watermark** _boolean_

  Whether to add a watermark to the generated video. Defaults to `false`.

- **audio** _boolean_

  Whether to generate audio (for I2V and R2V models that support it).

- **referenceUrls** _string[]_

  Array of reference image/video URLs for reference-to-video mode. Supports 0-5 images and 0-3 videos, max 5 total.

- **pollIntervalMs** _number_

  Polling interval in milliseconds for checking task status. Defaults to 5000.

- **pollTimeoutMs** _number_

  Maximum wait time in milliseconds for video generation. Defaults to 600000 (10 minutes).

<Note>
  Video generation is an asynchronous process that can take several minutes.
  Consider setting `pollTimeoutMs` to at least 10 minutes (600000ms) for
  reliable operation.
</Note>

### Video Model Capabilities

#### Text-to-Video

| Model                | Audio | Resolution        | Duration |
| -------------------- | ----- | ----------------- | -------- |
| `wan2.6-t2v`         | Yes   | 720P, 1080P       | 2-15s    |
| `wan2.5-t2v-preview` | Yes   | 480P, 720P, 1080P | 5s, 10s  |

#### Image-to-Video (First Frame)

| Model              | Audio    | Resolution  | Duration |
| ------------------ | -------- | ----------- | -------- |
| `wan2.6-i2v-flash` | Optional | 720P, 1080P | 2-15s    |
| `wan2.6-i2v`       | Yes      | 720P, 1080P | 2-15s    |

#### Reference-to-Video

| Model              | Audio    | Resolution  | Duration |
| ------------------ | -------- | ----------- | -------- |
| `wan2.6-r2v-flash` | Optional | 720P, 1080P | 2-10s    |
| `wan2.6-r2v`       | Yes      | 720P, 1080P | 2-10s    |

<Note>
  The tables above list models available in the Singapore International region.
  You can also pass any available provider model ID as a string if needed.
</Note>

## Model Capabilities

Please see the [Alibaba Cloud Model Studio docs](https://www.alibabacloud.com/help/en/model-studio/models) for a full
list of available models. You can also pass any available provider model ID as
a string if needed.

Reasoning

pnpm add @ai-sdk/alibaba

Provider 
Default provider instance


import { alibaba } from '@ai-sdk/alibaba';

Custom config
import { createAlibaba } from '@ai-sdk/alibaba';

const alibaba = createAlibaba({
  apiKey: process.env.ALIBABA_API_KEY ?? '',
});

Language  models

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








































































