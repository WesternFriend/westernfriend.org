"""Signals for pages whose contributors have asked to be excluded from AI use.

Excluded pages stay open to readers and search engines. See ADR 0006 and
docs/ai-opt-out.md.
"""

# IETF AI preferences (draft-ietf-aipref-vocab), as used by the Content-Usage
# HTTP header and the path-scoped Content-Usage rule in robots.txt
# (draft-ietf-aipref-attach). Content Signals has no documented per-path
# form, so robots.txt keeps its site-wide Content-Signal line.
AI_EXCLUDED_CONTENT_USAGE = "train-ai=n, ai-use=n, search=y"

# Crawlers that gather content for AI training or AI answers, not for a
# search index. robots.txt disallows excluded pages for these, since most AI
# crawlers honour Disallow but few read Content-Usage yet. Search crawlers
# such as Googlebot and Bingbot are deliberately absent.
AI_CRAWLER_USER_AGENTS = [
    "Amazonbot",
    "Applebot-Extended",
    "Bytespider",
    "CCBot",
    "ChatGPT-User",
    "Claude-SearchBot",
    "Claude-User",
    "ClaudeBot",
    "cohere-ai",
    "Google-Extended",
    "GPTBot",
    "meta-externalagent",
    "OAI-SearchBot",
    "Perplexity-User",
    "PerplexityBot",
]
