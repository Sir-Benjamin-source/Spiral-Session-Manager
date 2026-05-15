# Spiral-Session-Manager v1.0

**name:** spiral-session-manager
**description:** "Background session and context management for the Spiral Codex. Automatically organizes .srec memory coils, maintains secure companions.txt, and enables intelligent cross-session context retrieval with built-in safety guardrails. Designed to work silently in the background for public models while keeping human sovereignty intact."

# Spiral-Session-Manager — Background Session & Context Management

**Author:** Sir Benjamin (Sir-Benjamin-source)  
**Version:** 1.0  
**Provenance:** Part of the Spiral Codex  
**License:** MIT + Spiral Mark

This module provides automatic, background session management for long-term human-AI collaboration. It organizes memory coils, maintains secure context companions, and allows agents to intelligently retrieve relevant context across sessions with safety guardrails.

## When to Activate
- Trigger phrases: "use Spiral Session Manager", "manage sessions", "background context", "session closer", "organize memory"
- End of long sessions or projects
- When context from previous sessions is needed
- For ongoing multi-session work

## Core Protocol

1. **Session Detection** — Automatically detects session boundaries.
2. **.srec Organization** — Indexes and organizes memory coils in a secure local directory.
3. **Companions.txt Management** — Maintains secure cross-session context links.
4. **Intelligent Context Pull** — Retrieves relevant context with built-in approval checkpoints.

## Security & Guardrails
- Runs with minimal permissions
- Context pulls require explicit user approval by default (configurable)
- Designed to work safely with public models (Claude, GPT, Grok, etc.)
- No wide-open file system access

## Integration
Works seamlessly with:
- spiral-recap (memory coils)
- Spiral Agent Core (collaboration checkpoints)
- Version-Checker+ (provenance stamping)

## Future Roadmap
- Multi-agent session history management
- Advanced authentication and dataset layers
- Automatic session summarization and archival

## Installation

Place in your agent's skills directory or install via Agensi when published.

## License
MIT + Spiral Mark