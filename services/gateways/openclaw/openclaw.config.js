// openclaw.config.js
// Centralized hook configuration injected into the OpenClaw Node.js runtime.
module.exports = {
    plugins: [
        {
            id: 'metaclaw-routing-judge',
            hooks: {
                before_model_resolve: async (context) => {
                    console.error("[HOOK: routing-judge] Intercepting before model resolution...");
                    if (!context.messages || context.messages.length === 0) return context;

                    const lastMessage = context.messages[context.messages.length - 1];
                    const userPrompt = typeof lastMessage === 'object' ? (lastMessage.content || "") : "";
                    const agentId = context.agentId || "unknown";

                    // ==============================================================================
                    // STAGE 1: LEXICAL ROUTING (Fast-Path)
                    // ==============================================================================
                    if (userPrompt.includes("HEARTBEAT.md") || userPrompt.toLowerCase().includes("heartbeat")) {
                        console.error("[HOOK: routing-judge] LEXICAL MATCH: Heartbeat pattern detected.");
                        context.model = "litellm/simple-model";
                        return context;
                    }

                    // ==============================================================================
                    // STAGE 2: PREDICTIVE ROUTING (LLM-as-a-Judge)
                    // ==============================================================================
                    const judgeModel = process.env.OPENCLAW_JUDGE_MODEL;
                    const proxyUrl = process.env.OPENAI_BASE_URL || "http://active-proxy:4000/v1";
                    const masterKey = process.env.ACTIVE_PROXY_KEY || "";

                    if (!judgeModel || !masterKey) {
                        console.error("[HOOK: routing-judge] Infrastructure missing Judge Model or Master Key. Bypassing.");
                        return context;
                    }

                    const judgeSystemPrompt = `
You are an AI pipeline router. Evaluate the complexity of the user's prompt.
Output ONLY valid JSON in the following format: {"complexity": "simple" | "medium" | "complex" | "reasoning"}

Guidelines:
- "simple": Factual queries, basic translation, formatting.
- "medium": Summarization, basic scripting, drafting emails.
- "complex": System architecture, advanced coding, multi-step data pipelines.
- "reasoning": Mathematical proofs, paradox resolution, deep logic puzzles.
`;

                    const reqBody = {
                        model: judgeModel,
                        messages: [
                            { role: "system", content: judgeSystemPrompt },
                            { role: "user", content: `Agent Domain: ${agentId}\nPrompt: ${userPrompt}` }
                        ],
                        temperature: 0.0,
                        response_format: { type: "json_object" }
                    };

                    console.error(`[HOOK: routing-judge] Invoking Predictive Judge (${judgeModel}) via ${proxyUrl}...`);

                    try {
                        const controller = new AbortController();
                        const timeoutId = setTimeout(() => controller.abort(), 15000);

                        const response = await fetch(`${proxyUrl}/chat/completions`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${masterKey}`
                            },
                            body: JSON.stringify(reqBody),
                            signal: controller.signal
                        });

                        clearTimeout(timeoutId);

                        if (!response.ok) {
                            throw new Error(`HTTP status: ${response.status}`);
                        }

                        const data = await response.json();
                        const judgeOutput = data.choices[0].message.content;
                        console.error(`[HOOK: routing-judge] Judge Raw Output: ${judgeOutput}`);

                        const parsedOutput = JSON.parse(judgeOutput);
                        const complexity = parsedOutput.complexity || "medium";

                        const tierMapping = {
                            "simple": "litellm/simple-model",
                            "medium": "litellm/medium-model",
                            "complex": "litellm/complex-model",
                            "reasoning": "litellm/reasoning-model"
                        };

                        context.model = tierMapping[complexity] || "litellm/medium-model";
                        console.error(`[HOOK: routing-judge] Predictive Routing applied override: ${context.model}`);

                    } catch (err) {
                        console.error(`[HOOK: routing-judge] WARNING: Judge failed or timed out. Error: ${err.message}. Defaulting to medium.`);
                        context.model = "litellm/medium-model";
                    }

                    return context;
                }
            }
        }
    ]
};
