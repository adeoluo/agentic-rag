# Threat Model - Agentic RAG

## Assets

- Integrity of the retrieved evidence and the synthesized answer.

## Trust boundaries

- **Questions and documents are untrusted text.** They are tokenized and scored, never
  executed; there is no path from text to execution.

## Threats and mitigations

| Threat | Vector | Impact | Mitigation |
|---|---|---|---|
| Non-terminating retrieval | A follow-up keeps surfacing entities | Hang | Bounded hop budget; pivoted entities are not chased twice; seen queries are skipped |
| Index poisoning | Malicious documents added | Skewed answers | Retrieval is read-only over indexed text; callers control what is indexed |
| Misleading confidence | Thin evidence scored high | Overtrust | Confidence is a transparent term-coverage proxy, documented as such |
| Supply-chain compromise | Malicious dependency | Code execution | Zero runtime dependencies; Dependabot and CodeQL in continuous integration |

## Residual risk

Lexical retrieval cannot detect a semantically adversarial question that avoids all corpus
vocabulary; this is a capability limit, not a security control.
