// pass_through.js
// MetaClaw Pre-Packaged Routing Module: Pass-Through
//
// This module implements zero predictive routing. It relies entirely on the
// deterministic models you have hardcoded in your YAML profiles or explicit UI
// selections. This is the optimal configuration if you rely entirely on an
// external cloud routing layer (like OpenRouter's auto-fallback) or prefer
// 100% manual control over your token expenditure.

module.exports = {
    // Empty plugin payload. The hook interceptor is intentionally bypassed.
};
