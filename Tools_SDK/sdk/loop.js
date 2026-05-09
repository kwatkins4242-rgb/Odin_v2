import { ToolLoopAgent, tool } from 'ai';
import { z } from 'zod';

const codeAgent = new ToolLoopAgent({
    model: "anthropic/claude-sonnet-4.5",
    tools: {
        runCode: tool({
            description: 'Execute Python code',
            inputSchema: z.object({
                code: z.string(),
            }),
            execute: async ({ code }) => {
                // Execute code and return result
                return { output: 'Code executed successfully' };
            },
        }),
    },
});
