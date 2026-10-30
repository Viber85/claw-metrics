import deckyPlugin from "@decky/rollup";

// Decky's bundler resolves SteamUI/Decky globals instead of emitting
// CommonJS require() calls (which do not exist in the SteamUI runtime).
export default deckyPlugin({});
