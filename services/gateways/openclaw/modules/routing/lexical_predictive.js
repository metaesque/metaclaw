// lexical_predictive.js
// MetaClaw Native Workspace Plugin: Lexical + 3-Tier Predictive (INSTRUMENTED)

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

function logToStdout(msg) {
    process.stdout.write(`${msg}\n`);
}

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
    api.on('before_model_resolve', async (event) => {
        try {
            logToStdout("==================================================");
            logToStdout("[HOOK-DEBUG] 1. INVOCATION STARTED");

            // --- TIER 1 SPECIALTY MODEL BYPASS ---
            // Load routing metadata to determine if agent is a Team Lead
            const __dirname = path.dirname(fileURLToPath(import.meta.url));
            const metaPath = path.join(__dirname, 'routing_meta.json');
            let routingMeta = {};
            try {
                routingMeta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            } catch (e) {
                logToStdout(`[HOOK-DEBUG] Warning: Could not read routing_meta.json`);
            }

            // Extract agent ID safely based on OpenClaw's event schema
            const agentId = event.agentId || (event.session && event.session.agentId) || 'unknown';
            const isLead = routingMeta[agentId]?.is_lead;

            if (!isLead && agentId !== 'orchestrator' && agentId !== 'generalist') {
                logToStdout(`[HOOK-DEBUG] Agent '${agentId}' is a leaf node. Bypassing Predictive Judge to preserve specialty models.`);
                logToStdout("==================================================\n");
                return {};
            }

            const userPrompt = typeof event.prompt === 'string' ? event.prompt.trim() : JSON.stringify(event.prompt || "");
            logToStdout(`[HOOK-DEBUG] 2. Extracted prompt: "${userPrompt}"`);
            const promptLower = userPrompt.toLowerCase();

            // ==============================================================================
            // STAGE 1: LEXICAL ROUTING (Fast-Path)
            // ==============================================================================
            logToStdout(`[HOOK-DEBUG] 3. Checking lexical rules...`);
            if (/\bheartbeat\b/.test(promptLower) || promptLower.includes("heartbeat.md")) {
                logToStdout("[HOOK-DEBUG] >>> LEXICAL MATCH FOUND: heartbeat <<<");
                logToStdout("[HOOK-DEBUG] Returning { providerOverride: 'openai', modelOverride: 'simple-model' }");
                logToStdout("==================================================\n");
                return { providerOverride: "openai", modelOverride: "simple-model" };
            }

            logToStdout(`[HOOK-DEBUG] 4. No lexical match. Proceeding to Predictive Judge...`);
            const judgeModel = process.env.OPENCLAW_JUDGE_MODEL;
            const proxyUrl = process.env.OPENAI_BASE_URL || "http://active-proxy:4000/v1";
            const masterKey = process.env.ACTIVE_PROXY_KEY || "";

            if (!judgeModel || !masterKey) {
                logToStdout("[HOOK-DEBUG] Infrastructure missing Judge Model or Master Key. Bypassing.");
                return {};
            }

            const judgeSystemPrompt = `You are an AI pipeline router. Analyze the complexity of the user prompt.\nOutput ONLY valid JSON in the following format: {"complexity": "simple" | "medium" | "complex" | "frontier"}\n\nGuidelines:\n- "simple": Factual queries, basic translation, formatting, or trivial tool usage.\n- "medium": Summarization, standard business logic, drafting emails, moderate data parsing.\n- "complex": System architecture, advanced coding, mathematical proofs, multi-step data pipelines.\n- "frontier": Extreme context, zero-shot DAG generation, or advanced abstract reasoning.`;

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
                logToStdout(`[HOOK-DEBUG] Judge Raw Output: ${judgeOutput}`);

                const parsedOutput = JSON.parse(judgeOutput);
                const complexity = parsedOutput.complexity || "medium";

                const tierMapping = {
                    "simple": "simple-model",
                    "medium": "medium-model",
                    "complex": "complex-model",
                    "frontier": "frontier-model"
                };

                const chosenModel = tierMapping[complexity] || "medium-model";
                logToStdout(`[HOOK-DEBUG] Predictive Routing returning: openai / ${chosenModel}`);
                logToStdout("==================================================\n");
                return { providerOverride: "openai", modelOverride: chosenModel };

            } catch (err) {
                logToStdout(`[HOOK-DEBUG] WARNING: Judge failed or timed out. Error: ${err.message}. Defaulting to complex-model.`);
                logToStdout("==================================================\n");
                return { providerOverride: "openai", modelOverride: "complex-model" };
            }
        } catch (globalErr) {
            logToStdout(`\n[HOOK-DEBUG] !!! FATAL UNHANDLED ERROR IN HOOK !!!`);
            logToStdout(globalErr.stack || globalErr.message);
            logToStdout("==================================================\n");
            return {};
        }
    });
}

