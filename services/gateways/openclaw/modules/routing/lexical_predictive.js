// lexical_predictive.js
// MetaClaw Native Workspace Plugin: Lexical + 3-Tier Predictive (INSTRUMENTED)

function extractTextSafely(content) {
    if (!content) return "";
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) {
        return content
            .filter(item => item.type === 'text')
            .map(item => item.text)
            .join('\n');
    }
    return JSON.stringify(content);
}

export default function register(api) {
    api.on('before_model_resolve', async (context) => {
        try {
            console.error("\n==================================================");
            console.error("[HOOK-DEBUG] 1. INVOCATION STARTED");
            console.error(`[HOOK-DEBUG] Agent ID: ${context.agentId}`);
            console.error(`[HOOK-DEBUG] Current Model Target: ${context.model}`);

            if (!context.messages || context.messages.length === 0) {
                console.error("[HOOK-DEBUG] 2. No messages in context. Exiting.");
                return context;
            }

            console.error(`[HOOK-DEBUG] 3. Message chain length: ${context.messages.length}`);
            const userMessages = context.messages.filter(m => m.role === 'user');
            const lastUserMessage = userMessages.length > 0 ? userMessages[userMessages.length - 1] : null;

            if (!lastUserMessage) {
                console.error("[HOOK-DEBUG] 4. No user message found. (Likely a tool-resolution loop). Exiting.");
                return context;
            }

            console.error(`[HOOK-DEBUG] 5. Extracting text from last user message...`);
            console.error(`[HOOK-DEBUG] Raw content type: ${typeof lastUserMessage.content}`);

            let userPrompt = "";
            try {
                userPrompt = extractTextSafely(lastUserMessage.content).trim();
                console.error(`[HOOK-DEBUG] 6. Extracted prompt: "${userPrompt.substring(0, 100).replace(/\n/g, ' ')}"`);
            } catch (extractErr) {
                console.error(`[HOOK-DEBUG] ERROR in extractTextSafely: ${extractErr.message}`);
            }

            const promptLower = userPrompt.toLowerCase();

            console.error(`[HOOK-DEBUG] 7. Checking lexical rules...`);
            if (/\bheartbeat\b/.test(promptLower) || promptLower.includes("heartbeat.md")) {
                console.error("[HOOK-DEBUG] >>> LEXICAL MATCH FOUND: heartbeat <<<");
                context.model = "litellm/simple-model";
                console.error(`[HOOK-DEBUG] 8. Model reassigned to: ${context.model}`);
                console.error("==================================================\n");
                return context;
            }

            console.error(`[HOOK-DEBUG] 9. No lexical match. Proceeding to Predictive Judge...`);

            const judgeModel = process.env.OPENCLAW_JUDGE_MODEL;
            const proxyUrl = process.env.OPENAI_BASE_URL || "http://active-proxy:4000/v1";
            const masterKey = process.env.ACTIVE_PROXY_KEY || "";

            if (!judgeModel || !masterKey) {
                console.error("[HOOK-DEBUG] Infrastructure missing Judge Model or Master Key. Bypassing.");
                return context;
            }

            const recentContext = context.messages.slice(-4).map(msg => {
                return `${msg.role.toUpperCase()}: ${extractTextSafely(msg.content)}`;
            }).join('\n\n');

            const judgeSystemPrompt = `You are an AI pipeline router. Analyze the complexity of the recent conversation and the latest user prompt.\nOutput ONLY valid JSON in the following format: {"complexity": "simple" | "medium" | "complex"}\n\nGuidelines:\n- "simple": Factual queries, basic translation, formatting, or trivial tool usage.\n- "medium": Summarization, standard business logic, drafting emails, moderate data parsing.\n- "complex": System architecture, advanced coding, mathematical proofs, multi-step data pipelines.`;

            const reqBody = {
                model: judgeModel,
                messages: [
                    { role: "system", content: judgeSystemPrompt },
                    { role: "user", content: `Agent Domain: ${context.agentId || 'unknown'}\n\nRecent Conversation Context:\n${recentContext}\n\nAssess complexity.` }
                ],
                temperature: 0.0,
                response_format: { type: "json_object" }
            };

            console.error(`[HOOK-DEBUG] Invoking Predictive Judge (${judgeModel}) via ${proxyUrl}...`);

            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 8000);

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
                console.error(`[HOOK-DEBUG] Judge Raw Output: ${judgeOutput}`);

                const parsedOutput = JSON.parse(judgeOutput);
                const complexity = parsedOutput.complexity || "medium";

                const tierMapping = {
                    "simple": "litellm/simple-model",
                    "medium": "litellm/medium-model",
                    "complex": "litellm/complex-model"
                };

                context.model = tierMapping[complexity] || "litellm/medium-model";
                console.error(`[HOOK-DEBUG] Predictive Routing applied override: ${context.model}`);

            } catch (err) {
                console.error(`[HOOK-DEBUG] WARNING: Judge failed or timed out. Error: ${err.message}. Defaulting to complex.`);
                context.model = "litellm/complex-model";
            }

            console.error("==================================================\n");
        } catch (globalErr) {
            console.error(`\n[HOOK-DEBUG] !!! FATAL UNHANDLED ERROR IN HOOK !!!`);
            console.error(globalErr.stack || globalErr.message);
            console.error("==================================================\n");
        }
        return context;
    });
}
