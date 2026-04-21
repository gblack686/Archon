/**
 * Archive web conversations to a second-brain markdown vault.
 *
 * Fire-and-forget. Activates only when ARCHON_VAULT_DIR env is set.
 * Writes one markdown file per conversation into
 *   $ARCHON_VAULT_DIR/intelligence/archon-sessions/YYYY-MM-DD-<slug>.md
 *
 * Debounced per conversation: rewrites the file at most once every
 * ARCHON_ARCHIVE_DEBOUNCE_MS milliseconds (default 5000).
 */
import { mkdirSync, writeFileSync, existsSync, readFileSync, renameSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { createLogger } from '@archon/paths';
import { pool } from '../db/connection';

let cachedLog: ReturnType<typeof createLogger> | undefined;
function getLog(): ReturnType<typeof createLogger> {
  if (!cachedLog) cachedLog = createLogger('service.session-archiver');
  return cachedLog;
}

const DEBOUNCE_MS = Number(process.env.ARCHON_ARCHIVE_DEBOUNCE_MS ?? 5000);
const pending = new Map<string, NodeJS.Timeout>();

interface ConvRow {
  id: string;
  title: string | null;
  platform_type: string;
  codebase_id: string | null;
  created_at: string;
  last_activity_at: string;
}

interface MsgRow {
  role: 'user' | 'assistant';
  content: string;
  metadata: string;
  created_at: string;
}

/** Schedule (debounced) archive of one conversation. Safe to call on every message. */
export function scheduleArchive(conversationId: string): void {
  const vaultDir = process.env.ARCHON_VAULT_DIR;
  if (!vaultDir) return;

  const existing = pending.get(conversationId);
  if (existing) clearTimeout(existing);

  const t = setTimeout(() => {
    pending.delete(conversationId);
    archiveConversation(conversationId, vaultDir).catch(e => {
      const err = e as Error;
      getLog().warn(
        { conversationId, err, errorType: err.constructor.name },
        'archive.write_failed'
      );
    });
  }, DEBOUNCE_MS);

  // Don't block process exit on pending archives
  if (typeof t.unref === 'function') t.unref();
  pending.set(conversationId, t);
}

/** Force-flush: write archives for all pending conversations now. */
export async function flushArchives(): Promise<void> {
  const ids = [...pending.keys()];
  for (const id of ids) {
    const t = pending.get(id);
    if (t) clearTimeout(t);
    pending.delete(id);
  }
  const vaultDir = process.env.ARCHON_VAULT_DIR;
  if (!vaultDir) return;
  await Promise.all(ids.map(id => archiveConversation(id, vaultDir)));
}

async function archiveConversation(conversationId: string, vaultDir: string): Promise<void> {
  const convRes = await pool.query<ConvRow>(
    `SELECT id, title, platform_type, codebase_id, created_at, last_activity_at
     FROM remote_agent_conversations
     WHERE id = $1 AND deleted_at IS NULL`,
    [conversationId]
  );
  const conv = convRes.rows[0];
  if (!conv) return;

  const msgRes = await pool.query<MsgRow>(
    `SELECT role, content, metadata, created_at
     FROM remote_agent_messages
     WHERE conversation_id = $1
     ORDER BY created_at ASC`,
    [conversationId]
  );
  const msgs = msgRes.rows;
  if (msgs.length === 0) return;

  const outDir = join(resolve(vaultDir), 'intelligence', 'archon-sessions');
  mkdirSync(outDir, { recursive: true });

  const date = (conv.last_activity_at ?? conv.created_at).slice(0, 10);
  const slug = conv.id.slice(0, 8);
  const file = join(outDir, `${date}-${slug}.md`);

  const body = renderMarkdown(conv, msgs);
  const hash = createHash('sha1').update(body).digest('hex').slice(0, 8);

  // Skip if unchanged (hash in frontmatter)
  if (existsSync(file)) {
    try {
      const existing = readFileSync(file, 'utf8');
      if (existing.includes(`hash: ${hash}`)) return;
    } catch {
      /* fall through and rewrite */
    }
  }

  const front = [
    '---',
    `title: "${escapeYaml(conv.title ?? conv.id)}"`,
    `conversation_id: ${conv.id}`,
    `platform: ${conv.platform_type}`,
    `codebase_id: ${conv.codebase_id ?? ''}`,
    `created_at: ${conv.created_at}`,
    `last_activity_at: ${conv.last_activity_at}`,
    `message_count: ${msgs.length}`,
    `hash: ${hash}`,
    'source: archon',
    'tags: [archon-session]',
    '---',
    '',
  ].join('\n');

  // Atomic write: temp file + rename
  const tmp = `${file}.${randomUUID().slice(0, 8)}.tmp`;
  writeFileSync(tmp, front + body);
  renameSync(tmp, file);

  getLog().debug({ conversationId, file, messageCount: msgs.length }, 'archive.write_completed');
}

function renderMarkdown(conv: ConvRow, msgs: readonly MsgRow[]): string {
  const lines = [`# ${conv.title ?? conv.id}`, ''];
  for (const m of msgs) {
    const who = m.role === 'user' ? '**User**' : '**Assistant**';
    lines.push(`## ${who} — ${m.created_at}`, '', (m.content ?? '').trim(), '');
    if (m.metadata && m.metadata !== '{}') {
      try {
        const meta = JSON.parse(m.metadata) as { toolCalls?: unknown[] };
        if (Array.isArray(meta.toolCalls) && meta.toolCalls.length > 0) {
          lines.push(
            '<details><summary>tool calls</summary>',
            '',
            '```json',
            JSON.stringify(meta.toolCalls, null, 2),
            '```',
            '',
            '</details>',
            ''
          );
        }
      } catch {
        /* ignore malformed metadata JSON */
      }
    }
  }
  return lines.join('\n');
}

function escapeYaml(s: string): string {
  return s.replace(/"/g, '\\"').replace(/\n/g, ' ');
}
