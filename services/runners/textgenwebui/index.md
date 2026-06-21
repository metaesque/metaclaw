# textgenwebui: Text-Gen-WebUI

## Overview

Text-Gen-WebUI, affectionately known in the community as "Oobabooga", is a
Gradio-based web interface that serves as the Swiss Army knife of local LLMs. It
is designed for power users, researchers, and enthusiasts who want granular
control over every aspect of model inference.

Unlike tools that rely solely on GGUF/llama.cpp, Text-Gen-WebUI supports
bleeding-edge loaders like ExLlamaV2, AutoGPTQ, and AWQ. ExLlamaV2, in
particular, allows for incredibly fast inference of GPTQ/EXL2 models on modern
Nvidia GPUs, often vastly outperforming llama.cpp in tokens-per-second.

For OpenClaw users with high-end gaming PCs or multi-GPU rigs, Text-Gen-WebUI is
the ultimate backend. By loading an EXL2 model and enabling the WebUI's OpenAI
API extension, OpenClaw gains access to blistering fast generation speeds. This
makes complex agent tasks, such as recursive web searching and heavy
summarization, complete in a fraction of the time.
