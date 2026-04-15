// Auto-generated from library.yaml — regenerate with: python scripts/sync_library_json.py
// Last synced: 2026-04-14

export interface LibraryEntry {
  name: string;
  description: string;
  source: string;
  approved: boolean;
  usage: 'daily' | 'weekly' | 'monthly' | 'rare' | 'never';
  type: 'skill' | 'agent' | 'prompt';
  color: 'Blue' | 'Green' | 'Red' | 'Black' | 'White' | 'Colorless';
}

// MTG color assignment by keyword (matches expertise.yaml color_mapping)
function assignColor(entry: {
  name: string;
  description: string;
  type: string;
}): LibraryEntry['color'] {
  const text = `${entry.name} ${entry.description}`.toLowerCase();
  if (/github|git|ci\/cd|code|build|review|plan|hook|forge|cdk|plugin/.test(text)) return 'Blue';
  if (/aws|cloud|infra|lightsail|deploy|supabase/.test(text)) return 'Green';
  if (/obsidian|doc|knowledge|vault|schema|wiki|kb/.test(text)) return 'Red';
  if (/data|database|memory|graphiti|graph|pgvector|cost|track/.test(text)) return 'Black';
  if (/test|valid|admin|onboard|qa|audit/.test(text)) return 'White';
  return 'Colorless';
}

const rawSkills = [
  {
    name: 'daily-lesson',
    description: 'Trading: Daily TA Lesson - 30-day Kiyotaka curriculum delivered to Telegram',
    source: '~/.openclaw/workspace/skills/daily-lesson/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'domain-discovery',
    description: 'Meta-skill: Scan GitHub repos, discover domain areas, catalog in Obsidian',
    source: '~/.openclaw/workspace/skills/domain-discovery/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'expert-scheduler',
    description: 'Trading: Expert Scheduler - Start, stop, check status of 13 expert system jobs',
    source: '~/.openclaw/workspace/skills/expert-scheduler/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'gmail-inbox-monitor',
    description:
      'Monitor greg@gbautomation.xyz inbox every 5 min. Classifies, auto-labels, Telegram alerts',
    source: '~/.openclaw/workspace/skills/gmail-inbox-monitor/SKILL.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'linkedin-job-applier',
    description: 'Search LinkedIn Jobs, evaluate against criteria, apply via Easy Apply',
    source: '~/.openclaw/workspace/skills/linkedin-job-applier/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'linkedin-job-scanner',
    description: 'Scan LinkedIn messages for job opportunities ($175k+, remote)',
    source: '~/.openclaw/workspace/skills/linkedin-job-scanner/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'mac-mini-login',
    description:
      'Mac Mini access reference - SSH, OpenClaw gateway, agents, secrets, troubleshooting',
    source: '~/.openclaw/workspace/skills/mac-mini-login/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'onboarding',
    description:
      'Infrastructure: Harden OpenClaw config, validate API keys, set up extensions, health checks',
    source: '~/.openclaw/workspace/skills/onboarding/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'setup-openclaw',
    description:
      'Infrastructure: Install OpenClaw on Windows laptop, deploy workspace, configure secrets',
    source: '~/.openclaw/workspace/skills/setup-openclaw/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'back-tester',
    description: 'Trading: Backtesting suite - run backtests, optimize strategies, scout datasets',
    source:
      '~/repos/consulting-co/.claude/skills/consulting-intake/client-sessions/20260221-greg-trading/workspace/skills/back-tester/run-backtest/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'charting',
    description: 'Trading: Chart generation - equity curves, price charts',
    source:
      '~/repos/consulting-co/.claude/skills/consulting-intake/client-sessions/20260221-greg-trading/workspace/skills/charting/generate-chart/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'discord-scraping',
    description: 'Trading: Discord signal pipeline - scrape feeds, monitor, morning brief',
    source:
      '~/repos/consulting-co/.claude/skills/consulting-intake/client-sessions/20260221-greg-trading/workspace/skills/discord-scraping/scrape-discord/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'portfolio-manager',
    description: 'Trading: Portfolio management - monitor positions, manage risk, trade journal',
    source:
      '~/repos/consulting-co/.claude/skills/consulting-intake/client-sessions/20260221-greg-trading/workspace/skills/portfolio-manager/monitor-positions/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'consulting-intake',
    description:
      'Post-session transcript processor - extracts domains, builds workspace, generates skills',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/consulting-intake/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'intake-session-processor',
    description: 'Post-session transcript processor for GBAutomation consulting',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/intake-session-processor/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'skills-installer',
    description:
      'Transform workflow catalog entries into validated SKILL.md files with agent assignment',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/skills-installer/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'workflow-ideator',
    description: 'AI-generate workflow and skill ideas based on business domain, APIs, pain points',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/workflow-ideator/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'obsidian-vault',
    description: 'Obsidian vault management and knowledge base operations',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/obsidian-vault/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'obsidian-agent-archiver',
    description: 'Document AI agents, ADWs, skills into visual Obsidian knowledge base',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/obsidian-agent-archiver/SKILL.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'graphiti',
    description: 'Manage Graphiti knowledge graph MCP server for persistent AI memory',
    source: 'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/graphiti/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'tac-kb-query',
    description: 'Query TAC knowledge bases using Graphiti and pgvector for methodology learning',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/tac-kb-query/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'gmail-manager',
    description: 'Comprehensive Gmail management - summarization, contacts, newsletters, drafts',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/gmail-manager/SKILL.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'gmail-inbox-monitor-cc',
    description:
      'Monitor greg@gbautomation.xyz inbox - classify, auto-label, Telegram alerts (consulting-co version)',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/gmail-inbox-monitor/SKILL.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'aws-config-manager',
    description: 'AWS config management - credentials, secrets, billing, CloudWatch alerts',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/aws-config-manager/SKILL.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'github-issue-manager',
    description: 'GitHub issue management - create, monitor, analyze issues, track fixes',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/github-issue-manager/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'github-actions-manager',
    description: 'Manage GitHub Actions workflows, monitor CI/CD, trigger deployments',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/github-actions-manager/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'claude-code-plugin-builder',
    description: 'Build Claude Code marketplace plugins with guided workflow',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/claude-code-plugin-builder/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'client-linkedin',
    description: 'Quick LinkedIn professional overview for consulting intake',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/client-linkedin/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'client-personal-intel',
    description: 'Deep personal intelligence research - Instagram, YouTube, web presence analysis',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/client-personal-intel/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'consulting-admin',
    description: 'Consulting admin agent - client onboarding, Drive setup, email drafting',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/consulting-admin/SKILL.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'subscription-usage-checker',
    description:
      'Check credits, usage, costs across all subscriptions (Anthropic, AWS, OpenAI, etc.)',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/subscription-usage-checker/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'cost-tracker',
    description: 'Track and report AI service costs across providers',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/cost-tracker/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'create-second-brain-prd',
    description: 'Generate personalized Second Brain PRD from requirements template',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/create-second-brain-prd/SKILL.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'knowledge-sync',
    description: 'Sync knowledge across repos, Obsidian vaults, and agent workspaces',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/knowledge-sync/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'adw-dispatch',
    description: 'Dispatch autonomous development workflows (ADWs) to coding agents',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/adw-dispatch/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'plan-build-review-adw',
    description: 'Plan-Build-Review cycle for autonomous development workflows',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/plan-build-review-adw/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'adw-status',
    description: 'Check status of running autonomous development workflows',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/adw-status/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'worktree-manager',
    description: 'Manage git worktrees for parallel development',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/worktree-manager/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'linear-build-agent',
    description: 'Accept plan, create Linear project + issues, run autonomous coding sessions',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/linear-build-agent/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'revstar-quickstart-workflow',
    description: 'Guide users through AI developer workflows for RevStar QuickStart projects',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/revstar-quickstart-workflow/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'multi-agent-orchestrator-administration',
    description: 'Administer multi-agent orchestrator - agent config, monitoring, scaling',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/multi-agent-orchestrator-administration/SKILL.md',
    approved: false,
    usage: 'never' as const,
  },
  {
    name: 'github-cdk-workflows',
    description: 'GitHub CDK workflow construction and management',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/github-cdk-workflows/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'mtg-art-finder',
    description: 'Find Magic: The Gathering card art',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/mtg-art-finder/SKILL.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'gws-suite',
    description:
      'Full Google Workspace skill suite - Gmail, Drive, Calendar, Sheets, Docs, Chat, Meet, Forms, Slides, Keep, Scripts, + 30 recipes and 8 personas',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/gws/gws-workflow/SKILL.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'anthropic-memory',
    description:
      "Intelligent memory system using Anthropic's native Memory Tool for session tracking and entity extraction",
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/anthropic-memory/skill.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'obsidian-schema-generator',
    description:
      'Generate comprehensive schemas from Obsidian vaults - folder structure, note relationships, metadata, link graphs',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/obsidian-schema-generator/skill.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'browser-automation',
    description:
      'Browser automation and scraping framework - YouTube transcripts, TAC scanning, web research',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/browser-automation/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'skill-discovery',
    description:
      'Inventory all consulting pipeline skills, map to lifecycle phases, generate capabilities indexes',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/skill-discovery/SKILL.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'daily-client-logs',
    description:
      "Diff files across client workspace roots, detect changes, append dated activity log to each client's second brain",
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/daily-client-logs/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'team-runner',
    description: 'Plan, build, and run agent teams on Mac Mini through the Meridian pipeline',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/team-runner/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'social-media-recon',
    description:
      'Browser-native social media research - Instagram + Facebook profiles via Steer GUI automation',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/social-media-recon/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'graphify-sync',
    description:
      'Scan all client repos on Mac Mini, diff files since last run, re-run graphify --update on changed repos',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/graphify-sync/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'hooks',
    description:
      'Claude Code hooks framework - observability, security guards, agent team monitoring',
    source: 'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/hooks/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'mac-mini-codegen',
    description: 'Remote code generation on Mac Mini for agent tasks',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/mac-mini-codegen/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'tac-scaffolding',
    description: 'TAC scaffolding templates and patterns for agentic composition',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/tac-scaffolding/SKILL.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'client-research',
    description: 'Client research - Instagram deck builder, social discovery, competitive analysis',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/skills/client-research/SKILL.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'forge-tac-scan',
    description: 'Forge pre-flight scan - Search TAC repos for existing patterns before coding',
    source: '~/.openclaw/workspace/skills/forge-tac-scan/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
  {
    name: 'drive-claw-empire',
    description:
      'Drive Claw Empire - browser automation, API control, and Pi multi-team integration',
    source: '~/.openclaw/workspace/skills/drive-claw-empire/SKILL.md',
    approved: false,
    usage: 'rare' as const,
  },
];

const rawAgents = [
  {
    name: 'youtube-analysis-agent',
    description:
      'Transform raw transcripts into comprehensive insights with process flowcharts and Obsidian-formatted notes',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/youtube-analysis-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'youtube-transcript-agent',
    description: 'Browser-based YouTube transcript and description extractor when API methods fail',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/youtube-transcript-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'github-actions-agent',
    description: 'CI/CD pipeline management - workflows, runs, deployments, and failure analysis',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/github-actions-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'github-issue-agent',
    description: 'GitHub issue triage, analysis, and management agent',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/github-issue-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'obsidian-kb-expert',
    description:
      'Knowledge base expert for Obsidian vault architecture - taxonomies, schemas, CSS, Datacore, Dataview',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/obsidian-kb-expert.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'hooks-expert-agent',
    description:
      'Claude Code hooks implementation specialist - observability, security guards, lifecycle hooks',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/hooks-expert-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'aws-org-expert-agent',
    description:
      'AWS Organization expert - sub-accounts, Lightsail, cross-account IAM, least-privilege access',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/aws-org-expert-agent.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'supabase-expert-agent',
    description:
      'Supabase Vault expert - secrets management, health checks, migrations, encryption, RLS patterns',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/supabase-expert-agent.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'obsidian-expert-agent',
    description:
      'Obsidian vault expert - archive agents/skills/ADWs, frontmatter schemas, .base views, vault schemas',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/obsidian-expert-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'tac-expert-agent',
    description:
      'TAC agentic architecture composer - assembles blueprints of ADWs, hooks, agents, prompt templates, validation loops',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/tac-expert-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'openclaw-expert-agent',
    description:
      'OpenClaw expert - install, configure, manage on Lightsail, run tasks, deploy skills, manage gateway',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/openclaw-expert-agent.md',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'agent-browser-agent',
    description:
      'Headless browser automation via agent-browser (Vercel Labs) in WSL - web scraping, content extraction',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/agent-browser-agent.md',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'build-agent',
    description: 'Implement code based on approved plans following codebase patterns',
    source: 'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/build-agent.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'plan-agent',
    description:
      'Create detailed implementation plans with objectives, file changes, and acceptance criteria',
    source: 'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/plan-agent.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'review-agent',
    description: 'Review code changes against plan and produce risk-tiered report',
    source: 'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/review-agent.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'consulting-agent',
    description:
      'GBAutomation consulting operations - prospect research, onboarding, session processing, Drive/Gmail/Calendar',
    source:
      'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/consulting-agent.md',
    approved: true,
    usage: 'daily' as const,
  },
  {
    name: 'bowser-agent',
    description:
      'Unified browser automation - Chrome DevTools or Playwright, QA tests, scraping, screenshots',
    source: 'https://github.com/gblack686/consulting-co/blob/main/.claude/agents/bowser-agent.md',
    approved: true,
    usage: 'daily' as const,
  },
];

const rawPrompts = [
  {
    name: 'expert-tac',
    description:
      'TAC methodology expert - ADWs, hooks, agents, prompt templates, validation loops, plan-build-improve',
    source: 'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/tac/',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'expert-supabase',
    description:
      'Supabase expert - Vault secrets, database, health checks, migrations, encryption, RLS',
    source:
      'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/supabase/',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'expert-hooks',
    description:
      'Claude Code hooks expert - observability, security guards, lifecycle hooks, event forwarding',
    source: 'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/hooks/',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'expert-aws-org',
    description:
      'AWS Organization expert - sub-accounts, Lightsail, IAM policies, least-privilege access',
    source:
      'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/aws-org/',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'expert-obsidian',
    description:
      'Obsidian vault expert - taxonomies, schemas, CSS styles, Datacore, Dataview, AI-Agent-KB',
    source:
      'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/obsidian/',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'expert-openclaw',
    description:
      'OpenClaw expert - install, configure, manage, deploy skills, run tasks, Tailscale, gateway',
    source:
      'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/openclaw/',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'expert-linkedin',
    description:
      'LinkedIn expert - lead gen, credit system, browser automation, Sales Navigator, InMail',
    source:
      'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/linkedin/',
    approved: true,
    usage: 'weekly' as const,
  },
  {
    name: 'expert-pi',
    description:
      'Pi agent platform expert - extensions, tool definitions, session management, coding agent',
    source: 'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/pi/',
    approved: true,
    usage: 'monthly' as const,
  },
  {
    name: 'expert-bowser',
    description: 'Browser automation expert - Chrome DevTools, Playwright, QA testing patterns',
    source: 'https://github.com/gblack686/consulting-co/tree/main/.claude/commands/experts/bowser/',
    approved: true,
    usage: 'weekly' as const,
  },
];

export const libraryEntries: LibraryEntry[] = [
  ...rawSkills.map(s => ({
    ...s,
    type: 'skill' as const,
    color: assignColor({ ...s, type: 'skill' }),
  })),
  ...rawAgents.map(a => ({
    ...a,
    type: 'agent' as const,
    color: assignColor({ ...a, type: 'agent' }),
  })),
  ...rawPrompts.map(p => ({
    ...p,
    type: 'prompt' as const,
    color: assignColor({ ...p, type: 'prompt' }),
  })),
];

export const libraryStats = {
  total: libraryEntries.length,
  skills: rawSkills.length,
  agents: rawAgents.length,
  prompts: rawPrompts.length,
  approved: libraryEntries.filter(e => e.approved).length,
  daily: libraryEntries.filter(e => e.usage === 'daily').length,
};
