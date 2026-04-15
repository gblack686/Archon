import { useState, useMemo, useEffect } from 'react';
import {
  Search,
  BookOpen,
  Bot,
  Terminal,
  Zap,
  CheckCircle,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  X,
  Layers,
  Trash2,
  Copy,
  Check,
  Brain,
  Cpu,
  Globe,
  Shield,
  Wrench,
  Tag,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// === Types ===
interface LibraryEntry {
  name: string;
  description: string;
  source: string;
  approved: boolean;
  usage: string;
  type: 'skill' | 'agent' | 'prompt';
  category: string;
  color: string;
  frontmatter: Record<string, unknown>;
  body: string;
}

interface CatalogData {
  entries: LibraryEntry[];
  synced_at: string;
}

// === Constants ===
const TYPE_CONFIG = {
  skill: { icon: Zap, label: 'Skills', bg: 'bg-blue-100', text: 'text-blue-700' },
  agent: { icon: Bot, label: 'Agents', bg: 'bg-purple-100', text: 'text-purple-700' },
  prompt: { icon: Terminal, label: 'Experts', bg: 'bg-amber-100', text: 'text-amber-700' },
} as const;

const USAGE_COLORS: Record<string, string> = {
  daily: 'bg-emerald-100 text-emerald-700',
  weekly: 'bg-sky-100 text-sky-700',
  monthly: 'bg-violet-100 text-violet-700',
  rare: 'bg-zinc-100 text-zinc-500',
  never: 'bg-zinc-50 text-zinc-400',
};

const MTG_COLORS: Record<string, { border: string; dot: string }> = {
  Blue: { border: 'border-l-blue-400', dot: 'bg-blue-400' },
  Green: { border: 'border-l-emerald-400', dot: 'bg-emerald-400' },
  Red: { border: 'border-l-red-400', dot: 'bg-red-400' },
  Black: { border: 'border-l-zinc-600', dot: 'bg-zinc-600' },
  White: { border: 'border-l-amber-300', dot: 'bg-amber-300' },
  Colorless: { border: 'border-l-gray-300', dot: 'bg-gray-300' },
};

const CATEGORY_ORDER = [
  'Consulting Pipeline',
  'Communication',
  'Sales & Outbound',
  'Expert Systems',
  'Development Tools',
  'Knowledge Management',
  'Infrastructure',
  'Browser & Research',
  'Trading',
  'Operations',
  'Meta & Platform',
  'Other',
];

// === Smart Tags ===
const SMART_TAGS = [
  {
    id: 'memory',
    label: 'Memory',
    icon: Brain,
    color: 'bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200',
    match: /memory|graphiti|graph|knowledge.sync|vault|pgvector|obsidian.*schema|second.brain/i,
  },
  {
    id: 'hooks',
    label: 'Hooks',
    icon: Shield,
    color: 'bg-rose-100 text-rose-700 border-rose-200',
    match: /hook|lifecycle|observability|guard|event.*forward|pre.*tool|post.*tool/i,
  },
  {
    id: 'ai-agents',
    label: 'AI Agents',
    icon: Cpu,
    color: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    match: /agent|orchestrat|multi.agent|team.runner|adw|autonomous|claude.code|openclaw|meridian/i,
  },
  {
    id: 'browser',
    label: 'Browser',
    icon: Globe,
    color: 'bg-cyan-100 text-cyan-700 border-cyan-200',
    match: /browser|scrape|playwright|chrome|bowser|steer|screenshot|selenium/i,
  },
  {
    id: 'infra',
    label: 'Infrastructure',
    icon: Wrench,
    color: 'bg-orange-100 text-orange-700 border-orange-200',
    match: /aws|lightsail|docker|deploy|ci\/cd|github.action|cdk|infra/i,
  },
  {
    id: 'youtube',
    label: 'YouTube',
    icon: Tag,
    color: 'bg-red-100 text-red-700 border-red-200',
    match: /youtube|transcript|video|channel/i,
  },
  {
    id: 'google',
    label: 'Google',
    icon: Tag,
    color: 'bg-blue-100 text-blue-600 border-blue-200',
    match: /google|gmail|drive|calendar|sheets|docs|gws|workspace|meet|forms|slides|keep/i,
  },
  {
    id: 'supabase',
    label: 'Supabase',
    icon: Tag,
    color: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    match: /supabase|vault|rls|postgres|migration|encryption/i,
  },
  {
    id: 'archon',
    label: 'Archon',
    icon: Tag,
    color: 'bg-amber-100 text-amber-700 border-amber-200',
    match:
      /archon|workflow|worktree|isolation|slash.command|platform.adapter|conversation|codebase|remote.coding/i,
  },
] as const;

function getEntryTags(entry: LibraryEntry): string[] {
  const text = `${entry.name} ${entry.description}`;
  return SMART_TAGS.filter(tag => tag.match.test(text)).map(tag => tag.id);
}

// === Detail Panel ===
function DetailPanel({
  entry,
  onClose,
  onDelete,
}: {
  entry: LibraryEntry;
  onClose: () => void;
  onDelete: (name: string) => void;
}): React.ReactElement {
  const fm = entry.frontmatter;
  const hasFm = Object.keys(fm).length > 0;
  const hasBody = entry.body.length > 0;
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [copied, setCopied] = useState(false);

  const removeCmd = `python .claude/commands/experts/library/sync_viewer.py --remove ${entry.name}`;

  const handleCopy = (): void => {
    navigator.clipboard.writeText(removeCmd);
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  const handleDelete = (): void => {
    onDelete(entry.name);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />
      <div className="relative h-full w-full max-w-2xl overflow-y-auto border-l border-border bg-[var(--background)] shadow-xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-[var(--background)] px-6 py-4">
          <div className="flex items-center gap-3 min-w-0">
            {React.createElement(TYPE_CONFIG[entry.type].icon, {
              className: cn('h-5 w-5 shrink-0', TYPE_CONFIG[entry.type].text),
            })}
            <div className="min-w-0">
              <h2 className="text-base font-semibold text-text-primary truncate">{entry.name}</h2>
              <p className="text-[11px] text-text-tertiary truncate">
                {entry.category} &middot; {entry.type}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => {
                setConfirmDelete(!confirmDelete);
              }}
              className={cn(
                'rounded-md p-1.5 transition-colors',
                confirmDelete
                  ? 'bg-red-50 text-[var(--error)]'
                  : 'hover:bg-surface-hover text-text-tertiary hover:text-[var(--error)]'
              )}
              title="Delete entry"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              onClick={onClose}
              className="rounded-md p-1.5 hover:bg-surface-hover transition-colors"
            >
              <X className="h-4 w-4 text-text-tertiary" />
            </button>
          </div>
        </div>

        {/* Delete confirmation */}
        {confirmDelete && (
          <div className="mx-6 mt-4 rounded-md border border-[var(--error)]/30 bg-red-50 p-4 space-y-3">
            <p className="text-sm font-medium text-[var(--error)]">Delete "{entry.name}"?</p>
            <p className="text-xs text-text-secondary">
              This removes the entry from library.yaml, deletes the local skill/agent directory, and
              removes Obsidian notes.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 rounded bg-white px-2 py-1 text-[10px] font-mono text-text-secondary border border-border truncate">
                {removeCmd}
              </code>
              <button
                onClick={handleCopy}
                className="rounded p-1 hover:bg-white transition-colors"
                title="Copy command"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-[var(--success)]" />
                ) : (
                  <Copy className="h-3.5 w-3.5 text-text-tertiary" />
                )}
              </button>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleDelete}
                className="rounded-md bg-[var(--error)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--error)]/90 transition-colors"
              >
                Remove from viewer
              </button>
              <button
                onClick={() => {
                  setConfirmDelete(false);
                }}
                className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-surface-hover transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="px-6 py-5 space-y-5">
          {/* Description */}
          <p className="text-sm text-text-secondary leading-relaxed">{entry.description}</p>

          {/* Badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
                TYPE_CONFIG[entry.type].bg,
                TYPE_CONFIG[entry.type].text
              )}
            >
              {entry.type}
            </span>
            <span
              className={cn(
                'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
                USAGE_COLORS[entry.usage] ?? USAGE_COLORS.rare
              )}
            >
              {entry.usage}
            </span>
            {entry.approved && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                <CheckCircle className="h-3 w-3" /> Approved
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-xs text-text-tertiary border border-border/60">
              <span
                className={cn(
                  'h-2 w-2 rounded-full',
                  (MTG_COLORS[entry.color] ?? MTG_COLORS.Colorless).dot
                )}
              />
              {entry.color}
            </span>
          </div>

          {/* Source */}
          <div className="rounded-md border border-border bg-surface/50 p-3">
            <p className="text-[10px] uppercase tracking-widest text-text-tertiary mb-1">Source</p>
            {entry.source.startsWith('https://') ? (
              <a
                href={entry.source}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary hover:underline break-all flex items-center gap-1"
              >
                {entry.source} <ExternalLink className="h-3 w-3 shrink-0" />
              </a>
            ) : (
              <p className="text-xs text-text-secondary font-mono break-all">{entry.source}</p>
            )}
          </div>

          {/* Frontmatter */}
          {hasFm && (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-text-tertiary mb-2">
                Frontmatter
              </p>
              <div className="rounded-md border border-border bg-white p-3 space-y-1.5">
                {Object.entries(fm).map(([key, val]) => (
                  <div key={key} className="flex gap-2 text-xs">
                    <span className="font-mono text-primary shrink-0">{key}:</span>
                    <span className="text-text-secondary break-all">
                      {typeof val === 'object'
                        ? JSON.stringify(val)
                        : String(val as string | number | boolean)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Body content */}
          {hasBody ? (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-text-tertiary mb-2">
                Content
              </p>
              <div className="rounded-md border border-border bg-white p-4 text-xs text-text-secondary font-mono whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">
                {entry.body}
              </div>
            </div>
          ) : (
            <div className="rounded-md border border-dashed border-border p-4 text-center">
              <p className="text-xs text-text-tertiary">
                No local content resolved — source may be on a remote device
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// === Entry Card ===
function EntryCard({
  entry,
  onClick,
}: {
  entry: LibraryEntry;
  onClick: () => void;
}): React.ReactElement {
  const typeConf = TYPE_CONFIG[entry.type];
  const cardTypeIcon = typeConf.icon;
  const mtgColor = MTG_COLORS[entry.color] ?? MTG_COLORS.Colorless;
  const hasContent = entry.body.length > 0;
  const tags = getEntryTags(entry);

  return (
    <button
      onClick={onClick}
      className={cn(
        'group relative flex flex-col gap-2 rounded-lg border border-border/60 p-4 text-left transition-all hover:shadow-md hover:border-border cursor-pointer',
        'border-l-[3px]',
        mtgColor.border
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {React.createElement(cardTypeIcon, { className: cn('h-4 w-4 shrink-0', typeConf.text) })}
          <h3 className="text-sm font-semibold text-text-primary truncate">{entry.name}</h3>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {entry.approved && <CheckCircle className="h-3.5 w-3.5 text-[var(--success)]" />}
          {hasContent && <Layers className="h-3 w-3 text-text-tertiary opacity-40" />}
        </div>
      </div>
      <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
        {entry.description}
      </p>
      <div className="flex items-center gap-1.5 mt-auto pt-1">
        <span
          className={cn(
            'inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium',
            typeConf.bg,
            typeConf.text
          )}
        >
          {entry.type}
        </span>
        <span
          className={cn(
            'inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium',
            USAGE_COLORS[entry.usage] ?? USAGE_COLORS.rare
          )}
        >
          {entry.usage}
        </span>
        {tags.length > 0 &&
          tags.slice(0, 2).map(tid => {
            const t = SMART_TAGS.find(s => s.id === tid);
            if (!t) return null;
            return (
              <span
                key={tid}
                className={cn(
                  'inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[9px] font-medium',
                  t.color
                )}
              >
                {React.createElement(t.icon, { className: 'h-2.5 w-2.5' })}
                {t.label}
              </span>
            );
          })}
        <span className="ml-auto flex items-center gap-1 text-[10px] text-text-tertiary">
          <span className={cn('h-2 w-2 rounded-full', mtgColor.dot)} />
          {entry.color}
        </span>
      </div>
    </button>
  );
}

// === Category Section ===
function CategorySection({
  category,
  entries,
  onSelect,
}: {
  category: string;
  entries: LibraryEntry[];
  onSelect: (e: LibraryEntry) => void;
}): React.ReactElement {
  const [collapsed, setCollapsed] = useState(false);
  const approved = entries.filter(e => e.approved).length;

  return (
    <div>
      <button
        onClick={() => {
          setCollapsed(!collapsed);
        }}
        className="flex items-center gap-2 w-full text-left mb-2 group"
      >
        {collapsed ? (
          <ChevronRight className="h-4 w-4 text-text-tertiary" />
        ) : (
          <ChevronDown className="h-4 w-4 text-text-tertiary" />
        )}
        <h2 className="text-sm font-semibold text-text-primary">{category}</h2>
        <span className="text-[10px] text-text-tertiary">
          {entries.length} {entries.length === 1 ? 'entry' : 'entries'} &middot; {approved} approved
        </span>
      </button>
      {!collapsed && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 mb-6">
          {entries.map(entry => (
            <EntryCard
              key={`${entry.type}-${entry.name}`}
              entry={entry}
              onClick={() => {
                onSelect(entry);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// === Main Page ===
export function LibraryPage(): React.ReactElement {
  const [catalog, setCatalog] = useState<CatalogData | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());
  const [approvedOnly, setApprovedOnly] = useState(false);
  const [selected, setSelected] = useState<LibraryEntry | null>(null);

  const toggleTag = (id: string): void => {
    setActiveTags(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  useEffect(() => {
    fetch('/library-catalog.json')
      .then(r => r.json())
      .then((data: CatalogData) => {
        setCatalog(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const filtered = useMemo(() => {
    if (!catalog) return [];
    return catalog.entries.filter(entry => {
      if (typeFilter !== 'all' && entry.type !== typeFilter) return false;
      if (approvedOnly && !entry.approved) return false;
      if (activeTags.size > 0) {
        const entryTags = getEntryTags(entry);
        if (![...activeTags].some(t => entryTags.includes(t))) return false;
      }
      if (search) {
        const q = search.toLowerCase();
        return entry.name.toLowerCase().includes(q) || entry.description.toLowerCase().includes(q);
      }
      return true;
    });
  }, [catalog, search, typeFilter, approvedOnly, activeTags]);

  const grouped = useMemo(() => {
    const map = new Map<string, LibraryEntry[]>();
    for (const entry of filtered) {
      const cat = entry.category || 'Other';
      const existing = map.get(cat);
      if (existing) {
        existing.push(entry);
      } else {
        map.set(cat, [entry]);
      }
    }
    // Sort by CATEGORY_ORDER
    return CATEGORY_ORDER.filter(cat => map.has(cat)).map(cat => ({
      category: cat,
      entries: map.get(cat) ?? [],
    }));
  }, [filtered]);

  const stats = useMemo(() => {
    if (!catalog) return { total: 0, skills: 0, agents: 0, prompts: 0, approved: 0 };
    const entries = catalog.entries;
    return {
      total: entries.length,
      skills: entries.filter(e => e.type === 'skill').length,
      agents: entries.filter(e => e.type === 'agent').length,
      prompts: entries.filter(e => e.type === 'prompt').length,
      approved: entries.filter(e => e.approved).length,
    };
  }, [catalog]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-sm text-text-tertiary">Loading catalog...</div>
      </div>
    );
  }

  if (!catalog) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3">
        <BookOpen className="h-10 w-10 text-text-tertiary opacity-40" />
        <p className="text-sm text-text-tertiary">No catalog found. Run the sync script:</p>
        <code className="rounded bg-surface px-3 py-1.5 text-xs font-mono text-text-secondary">
          python .claude/commands/experts/library/sync_viewer.py
        </code>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 pt-5 pb-3">
        <div>
          <h1 className="text-lg font-semibold text-text-primary">The Library</h1>
          <p className="text-xs text-text-tertiary mt-0.5">
            {stats.total} entries &mdash; {stats.skills} skills, {stats.agents} agents,{' '}
            {stats.prompts} experts
          </p>
        </div>
        <div className="hidden md:flex items-center gap-3 text-[10px] uppercase tracking-widest text-text-tertiary">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[var(--success)]" />
            {stats.approved} approved
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
            {filtered.length} shown
          </span>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 px-6 pb-3 border-b border-border/60">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-tertiary" />
          <input
            type="text"
            placeholder="Search skills, agents, experts..."
            value={search}
            onChange={e => {
              setSearch(e.target.value);
            }}
            className="w-full rounded-md border border-border bg-white/60 py-1.5 pl-8 pr-3 text-xs text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-primary/40"
          />
        </div>
        <div className="flex items-center rounded-md border border-border bg-white/40 p-0.5">
          {(['all', 'skill', 'agent', 'prompt'] as const).map(t => (
            <button
              key={t}
              onClick={() => {
                setTypeFilter(t);
              }}
              className={cn(
                'rounded px-2.5 py-1 text-[11px] font-medium transition-colors',
                typeFilter === t
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              )}
            >
              {t === 'all' ? 'All' : TYPE_CONFIG[t].label}
            </button>
          ))}
        </div>
        <button
          onClick={() => {
            setApprovedOnly(!approvedOnly);
          }}
          className={cn(
            'flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[11px] font-medium transition-colors',
            approvedOnly
              ? 'border-[var(--success)] bg-emerald-50 text-[var(--success)]'
              : 'border-border text-text-tertiary hover:text-text-secondary'
          )}
        >
          <CheckCircle className="h-3 w-3" />
          Approved
        </button>
        <span className="h-4 w-px bg-border/60 mx-1" />
        {SMART_TAGS.map(tag => {
          const filterTagIcon = tag.icon;
          const active = activeTags.has(tag.id);
          return (
            <button
              key={tag.id}
              onClick={() => {
                toggleTag(tag.id);
              }}
              className={cn(
                'flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors',
                active
                  ? tag.color + ' border-current shadow-sm'
                  : 'border-border text-text-tertiary hover:text-text-secondary bg-white/40'
              )}
            >
              {React.createElement(filterTagIcon, { className: 'h-3 w-3' })}
              {tag.label}
            </button>
          );
        })}
        <span className="text-[10px] text-text-tertiary ml-auto">
          {grouped.reduce((sum, g) => sum + g.entries.length, 0)} results in {grouped.length} groups
        </span>
      </div>

      {/* Grouped card grid */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {grouped.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-text-tertiary">
            <BookOpen className="h-10 w-10 mb-3 opacity-40" />
            <p className="text-sm">No entries match your filters</p>
          </div>
        ) : (
          grouped.map(({ category, entries }) => (
            <CategorySection
              key={category}
              category={category}
              entries={entries}
              onSelect={setSelected}
            />
          ))
        )}
      </div>

      {/* Detail slide-over */}
      {selected && (
        <DetailPanel
          entry={selected}
          onClose={() => {
            setSelected(null);
          }}
          onDelete={name => {
            // Remove from local state immediately; run sync script to persist
            setCatalog(prev =>
              prev
                ? {
                    ...prev,
                    entries: prev.entries.filter(e => e.name !== name),
                  }
                : null
            );
          }}
        />
      )}
    </div>
  );
}
