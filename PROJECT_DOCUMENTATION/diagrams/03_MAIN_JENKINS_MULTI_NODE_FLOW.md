# 03 — Main Jenkins Multi-Node Flow

```mermaid
flowchart TD
    C[Jenkins Controller<br/>Jenkinsfile: agent none] --> VS[Validate Selection<br/>agent any]
    VS --> R{DATABASE + ACTION}
    R -->|MYSQL / MSSQL| UB[agent: ubuntu-node]
    R -->|MONGODB / POSTGRESQL| WIN[agent: windows-node]
    UB --> EP1[executePipeline:<br/>RBAC auth+authz, logger init, body, finalize, report]
    WIN --> EP2[executePipeline:<br/>RBAC auth+authz, logger init, body, finalize, report]
    EP1 --> SCR[DB/OS batch|bash scripts]
    EP2 --> SCR
    SCR --> DB[(Database)]
```
