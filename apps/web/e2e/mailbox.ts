/** Reads emails captured by Supabase local (Mailpit). Local development only. */

const MAILPIT = process.env.E2E_MAILPIT_URL ?? "http://127.0.0.1:54324";

type MessageSummary = { ID: string };

export async function waitForLink(to: string, pathFragment: string): Promise<string> {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    const search = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:${to}`)}`);
    const { messages } = (await search.json()) as { messages: MessageSummary[] };
    for (const message of messages) {
      const detail = await fetch(`${MAILPIT}/api/v1/message/${message.ID}`);
      const { HTML } = (await detail.json()) as { HTML: string };
      const match = HTML.match(/href="([^"]+)"/g)
        ?.map((attribute) => attribute.slice(6, -1).replaceAll("&amp;", "&"))
        .find((href) => href.includes(pathFragment));
      if (match) return match;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`No email with a ${pathFragment} link arrived for ${to}`);
}
