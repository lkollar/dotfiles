import { tool } from "@opencode-ai/plugin"

const SEARXNG_URL = "http://10.0.1.2:8084/search"

export default tool({
  description: "Search the web for information using SearXNG",
  args: {
    query: tool.schema.string().describe("Search query"),
  },
  async execute(args) {
    const reachable = await Bun.$`curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 ${SEARXNG_URL}`.quiet().then(r => r.stdout as string === "200").catch(() => false)
    if (!reachable) {
      return "SearXNG is not available (off home network). Use webfetch with a search engine URL like https://duckduckgo.com/?q=... instead."
    }
    const url = `${SEARXNG_URL}?q=${encodeURIComponent(args.query)}&format=json`
    const { stdout } = await Bun.$`curl -s ${url}`.quiet()
    const data = JSON.parse(stdout as string)
    const results = (data.results || []).slice(0, 10)
    if (results.length === 0) {
      return "No results found."
    }
    return results
      .map((r: any, i: number) =>
        `${i + 1}. ${r.title}\n   ${r.url}\n   ${r.content || r.snippet || ""}`
      )
      .join("\n\n")
  },
})
