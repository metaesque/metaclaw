// lexical_predictive.js
// MetaClaw Native Workspace Plugin: Lexical + 3-Tier Predictive (INSTRUMENTED)

/**
 * Helper to force logs into the Docker stdout stream so they don't get
 * swallowed by OpenClaw's internal async log formatting.
 */
function logToStdout(msg) {
    process.stdout.write(`\n${msg}\n`);
}

export default function register(api) {
    api.on('before_model_resolve', async (event) => {
        try {
            logToStdout("==================================================");
            logToStdout("[HOOK-DEBUG] 1. INVOCATION STARTED");

            // Dump the absolute ground truth of the event structure
            logToStdout("[HOOK-DEBUG] RAW EVENT STRUCTURE:");
            logToStdout(JSON.stringify(event, null, 2));

            // Extract the prompt using the official schema
            const userPrompt = typeof event.prompt === 'string' ? event.prompt.trim() : JSON.stringify(event.prompt || "");
            logToStdout(`[HOOK-DEBUG] 2. Extracted prompt: "${userPrompt}"`);

            const promptLower = userPrompt.toLowerCase();

            // ==============================================================================
            // STAGE 1: LEXICAL ROUTING (Fast-Path)
            // ==============================================================================
            logToStdout(`[HOOK-DEBUG] 3. Checking lexical rules...`);
            if (/\bheartbeat\b/.test(promptLower) || promptLower.includes("heartbeat.md")) {
                logToStdout("[HOOK-DEBUG] >>> LEXICAL MATCH FOUND: heartbeat <<<");
                logToStdout("[HOOK-DEBUG] Returning modelOverride: litellm/simple-model");
                logToStdout("==================================================\n");
                // OpenClaw API mandates returning the override object, not mutating the event
                return { modelOverride: "litellm/simple-model" };
            }

            logToStdout(`[HOOK-DEBUG] 4. No lexical match. Proceeding to Predictive Judge...`);

            const judgeModel = process.env.OPENCLAW_JUDGE_MODEL;
            const proxyUrl = process.env.OPENAI_BASE_URL || "http://active-proxy:4000/v1";
            const masterKey = process.env.ACTIVE_PROXY_KEY || "";

            if (!judgeModel || !masterKey) {
                logToStdout("[HOOK-DEBUG] Infrastructure missing Judge Model or Master Key. Bypassing.");
                return {};
            }

            // Since before_model_resolve only receives the current prompt, we judge it directly.
            const judgeSystemPrompt = `You are an AI pipeline router. Analyze the complexity of the user prompt.\nOutput ONLY valid JSON in the following format: {"complexity": "simple" | "medium" | "complex"}\n\nGuidelines:\n- "simple": Factual queries, basic translation, formatting, or trivial tool usage.\n- "medium": Summarization, standard business logic, drafting emails, moderate data parsing.\n- "complex": System architecture, advanced coding, mathematical proofs, multi-step data pipelines.`;

            const reqBody = {
                model: judgeModel,
                messages: [
                    { role: "system", content: judgeSystemPrompt },
                    { role: "user", content: `Prompt:\n${userPrompt}\n\nAssess complexity.` }
                ],
                temperature: 0.0,
                response_format: { type: "json_object" }
            };

            logToStdout(`[HOOK-DEBUG] Invoking Predictive Judge (${judgeModel}) via ${proxyUrl}...`);

            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 8000); // Strict 8s timeout

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
                logToStdout(`[HOOK-DEBUG] Judge Raw Output: ${judgeOutput}`);

                const parsedOutput = JSON.parse(judgeOutput);
                const complexity = parsedOutput.complexity || "medium";

                const tierMapping = {
                    "simple": "litellm/simple-model",
                    "medium": "litellm/medium-model",
                    "complex": "litellm/complex-model"
                };

                const chosenModel = tierMapping[complexity] || "litellm/medium-model";
                logToStdout(`[HOOK-DEBUG] Predictive Routing returning modelOverride: ${chosenModel}`);
                logToStdout("==================================================\n");
                return { modelOverride: chosenModel };

            } catch (err) {
                logToStdout(`[HOOK-DEBUG] WARNING: Judge failed or timed out. Error: ${err.message}. Defaulting to complex.`);
                logToStdout("==================================================\n");
                return { modelOverride: "litellm/complex-model" };
            }
        } catch (globalErr) {
            logToStdout(`\n[HOOK-DEBUG] !!! FATAL UNHANDLED ERROR IN HOOK !!!`);
            logToStdout(globalErr.stack || globalErr.message);
            logToStdout("==================================================\n");
            return {};
        }
    });
}
