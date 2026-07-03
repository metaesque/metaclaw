// lexical_predictive.js
// MetaClaw Native Workspace Plugin: Lexical + 3-Tier Predictive
//
// This module provides a dual-layer routing strategy. It first checks for hardcoded
// string matches (Lexical Fast-Path) to bypass API calls. If no match is found,
// it extracts recent conversation history and asks a fast, local LLM to score
// the prompt's complexity as 'simple', 'medium', or 'complex'.

/**
 * Safely extracts pure text from an OpenClaw message payload.
 * OpenClaw messages can contain nested arrays (e.g., tool outputs or images).
 * This prevents the judge model from crashing on "[object Object]" strings.
 */
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

/**
 * Helper to force logs into the Docker stdout stream so they don't get
 * swallowed by OpenClaw's internal async log formatting.
 */
function logToStdout(msg) {
    process.stdout.write(`\n${msg}\n`);
}

// Native OpenClaw Plugin API Entrypoint
export default function register(api) {
    api.on('before_model_resolve', async (context) => {
        logToStdout("[HOOK: lexical-predictive] Intercepting before model resolution...");
        if (!context.messages || context.messages.length === 0) return context;

        // Extract the LAST ACTUAL USER MESSAGE to avoid evaluating tool_result JSON blobs during execution loops
        const userMessages = context.messages.filter(m => m.role === 'user');
        const lastUserMessage = userMessages.length > 0 ? userMessages[userMessages.length - 1] : null;

        if (!lastUserMessage) {
            logToStdout("[HOOK: lexical-predictive] No user message found in context. Bypassing.");
            return context;
        }

        const userPrompt = extractTextSafely(lastUserMessage.content).trim();
        const agentId = context.agentId || "unknown";

        // ==============================================================================
        // STAGE 1: LEXICAL ROUTING (Fast-Path)
        // ==============================================================================
        const promptLower = userPrompt.toLowerCase();

        // Media Modality Overrides
        if (promptLower.startsWith("new sfw image")) {
            logToStdout("[HOOK: lexical-predictive] LEXICAL MATCH: Routing to SFW Image model.");
            context.model = "litellm/flux-1-dev";
            return context;
        }
        if (promptLower.startsWith("new nsfw image")) {
            logToStdout("[HOOK: lexical-predictive] LEXICAL MATCH: Routing to NSFW Image model.");
            context.model = "litellm/pony-diffusion-v6-xl";
            return context;
        }

        // Trivial Fast-Paths (Regex boundary check for resilience)
        if (/\bheartbeat\b/.test(promptLower) || promptLower.includes("heartbeat.md")) {
            logToStdout("[HOOK: lexical-predictive] LEXICAL MATCH: Heartbeat pattern detected. Routing to litellm/simple-model");
            context.model = "litellm/simple-model";
            return context;
        }

        // ==============================================================================
        // STAGE 2: PREDICTIVE ROUTING (LLM-as-a-Judge)
        // ==============================================================================
        const judgeModel = process.env.OPENCLAW_JUDGE_MODEL;
        // Fix for Node 18+ fetch Docker DNS resolution: Force 127.0.0.1 mapping or explicit active-proxy
        const proxyUrl = process.env.OPENAI_BASE_URL || "http://active-proxy:4000/v1";
        const masterKey = process.env.ACTIVE_PROXY_KEY || "";

        if (!judgeModel || !masterKey) {
            logToStdout("[HOOK: lexical-predictive] Infrastructure missing Judge Model or Master Key. Bypassing.");
            return context;
        }

        // Extract the last 4 messages to cure "Context Blindness"
        const recentContext = context.messages.slice(-4).map(msg => {
            return `${msg.role.toUpperCase()}: ${extractTextSafely(msg.content)}`;
        }).join('\n\n');

        const judgeSystemPrompt = `You are an AI pipeline router. Analyze the complexity of the recent conversation and the latest user prompt.\nOutput ONLY valid JSON in the following format: {"complexity": "simple" | "medium" | "complex"}\n\nGuidelines:\n- "simple": Factual queries, basic translation, formatting, or trivial tool usage.\n- "medium": Summarization, standard business logic, drafting emails, moderate data parsing.\n- "complex": System architecture, advanced coding, mathematical proofs, multi-step data pipelines.`;

        const reqBody = {
            model: judgeModel,
            messages: [
                { role: "system", content: judgeSystemPrompt },
                { role: "user", content: `Agent Domain: ${agentId}\n\nRecent Conversation Context:\n${recentContext}\n\nAssess complexity.` }
            ],
            temperature: 0.0,
            response_format: { type: "json_object" }
        };

        logToStdout(`[HOOK: lexical-predictive] Invoking Predictive Judge (${judgeModel}) via ${proxyUrl}...`);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000); // Strict 8s timeout to prevent stall

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
            logToStdout(`[HOOK: lexical-predictive] Judge Raw Output: ${judgeOutput}`);

            const parsedOutput = JSON.parse(judgeOutput);
            const complexity = parsedOutput.complexity || "medium";

            const tierMapping = {
                "simple": "litellm/simple-model",
                "medium": "litellm/medium-model",
                "complex": "litellm/complex-model"
            };

            context.model = tierMapping[complexity] || "litellm/medium-model";
            logToStdout(`[HOOK: lexical-predictive] Predictive Routing applied override: ${context.model}`);

        } catch (err) {
            logToStdout(`[HOOK: lexical-predictive] WARNING: Judge failed or timed out. Error: ${err.message}. Defaulting to complex.`);
            // Fail-safe to complex to ensure tasks complete even if the local judge node crashes
            context.model = "litellm/complex-model";
        }

        return context;
    });
}
