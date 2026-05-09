
import { ToolLoopAgent } from 'ai';

const myAgent = new ToolLoopAgent({
    model: "anthropic/claude-sonnet-4.5",
    instructions: 'You are a helpful assistant.',
    tools: {
        // Your tools here
    },
});




