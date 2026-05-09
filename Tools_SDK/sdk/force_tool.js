

import { ToolLoopAgent } from 'ai';

const agent = new ToolLoopAgent({
    model: "anthropic/claude-sonnet-4.5",
    tools: {
        weather: weatherTool,
        cityAttractions: attractionsTool,
    },
    toolChoice: {
        type: 'tool',
        toolName: 'weather', // Force the weather tool to be used
    },
});
