#!/usr/bin/env bun
// Export archon web conversations → second-brain as markdown.
// Usage:
//   bun run scripts/archon-session-archive.mjs                  # export all (skips unchanged)
//   bun run scripts/archon-session-archive.mjs --conv <id>      # single conversation
//   bun run scripts/archon-session-archive.mjs --since 2026-04-01
//
// Env:
//   VAULT_DIR  absolute path to second-brain root
//              default: ~/.archon/workspaces/gbauto/jid5274/source/second-brain

import { Database } from 'bun:sqlite';
import { mkdirSync, writeFileSync, existsSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';

const DB_PATH = process.env.ARCHON_DB ?? resolve(homedir(), '.archon/archon.db');
const VAULT_DIR = process.env.VAULT_DIR ?? resolve(
  homedir(),
  '.archon/workspaces/gbauto/jid5274/source/second-brain',
);
const OUT_DIR = join(VAULT_DIR, 'intelligence', 'archon-sessions');

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => {
    if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1]?.startsWith('--') ? true : arr[i + 1]]);
    return acc;
  }, []),
);

const db = new Database(DB_PATH, { readonly: true });
mkdirSync(OUT_DIR, { recursive: true });

const where = [];
const params = {};
if (args.conv) { where.push('id = $id'); params.$id = args.conv; }
if (args.since) { where.push('last_activity_at >= $since'); params.$since = args.since; }
where.push('deleted_at IS NULL');

const convs = db.prepare(
  `SELECT id, title, platform_type, codebase_id, created_at, last_activity_at
   FROM remote_agent_conversations
   WHERE ${where.join(' AND ')}
   ORDER BY last_activity_at DESC`,
).all(params);

const msgStmt = db.prepare(
  `SELECT role, content, metadata, created_at
   FROM remote_agent_messages
   WHERE conversation_id = $id
   ORDER BY created_at ASC`,
);

let written = 0, skipped = 0;
for (const c of convs) {
  const msgs = msgStmt.all({ $id: c.id });
  if (msgs.length === 0) { skipped++; continue; }

  const date = (c.last_activity_at ?? c.created_at).slice(0, 10);
  const slug = c.id.slice(0, 8);
  const file = join(OUT_DIR, `${date}-${slug}.md`);

  const body = renderMarkdown(c, msgs);
  const hash = createHash('sha1').update(body).digest('hex').slice(0, 8);

  // Skip if unchanged (hash stored in frontmatter)
  if (existsSync(file)) {
    const existing = readFileSync(file, 'utf8');
    if (existing.includes(`hash: ${hash}`)) { skipped++; continue; }
  }

  const front = [
    '---',
    `title: "${escapeYaml(c.title ?? c.id)}"`,
    `conversation_id: ${c.id}`,
    `platform: ${c.platform_type}`,
    `codebase_id: ${c.codebase_id ?? ''}`,
    `created_at: ${c.created_at}`,
    `last_activity_at: ${c.last_activity_at}`,
    `message_count: ${msgs.length}`,
    `hash: ${hash}`,
    'source: archon',
    'tags: [archon-session]',
    '---',
    '',
  ].join('\n');

  writeFileSync(file, front + body);
  written++;
}

console.log(`archon-archive: wrote ${written}, skipped ${skipped} (total ${convs.length}) → ${OUT_DIR}`);

function renderMarkdown(c, msgs) {
  const lines = [`# ${c.title ?? c.id}`, ''];
  for (const m of msgs) {
    const who = m.role === 'user' ? '**User**' : m.role === 'assistant' ? '**Assistant**' : `**${m.role}**`;
    lines.push(`## ${who} — ${m.created_at}`, '', m.content?.trim() ?? '', '');
    if (m.metadata) {
      try {
        const meta = JSON.parse(m.metadata);
        if (meta.toolCalls?.length) {
          lines.push('<details><summary>tool calls</summary>', '', '```json', JSON.stringify(meta.toolCalls, null, 2), '```', '', '</details>', '');
        }
      } catch { /* ignore bad json */ }
    }
  }
  return lines.join('\n');
}

function escapeYaml(s) {
  return String(s).replace(/"/g, '\\"').replace(/\n/g, ' ');
}
