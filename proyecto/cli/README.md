# Edge Clean Copilot CLI

Command-line interface for **Edge Clean Copilot**, implementing the **Ports & Adapters (Hexagonal) Architecture** to ensure complete decoupling between core business logic and local language model inference engines.

---

## 1. Architectural Layers

```
proyecto/cli/src/
├── domain/                    # Pure business logic and invariants
│   └── entities/
│       └── SourceFile.ts      # Validates file size, extensions, and immutability
│
├── application/               # Application orchestration and interfaces
│   ├── dtos/
│   │   └── RefactorDTO.ts     # Input and output boundary data transfers
│   ├── ports/
│   │   └── IInferenceEngine.ts # Primary outbound inference port contract
│   └── use-cases/
│       └── RefactorCodeUseCase.ts # Orchestrates domain verification and inference
│
├── infrastructure/            # Concrete adapters and I/O implementations
│   ├── ai/
│   │   ├── MockInferenceAdapter.ts # Deterministic offline adapter for unit testing
│   │   └── LlamaServerAdapter.ts   # HTTP adapter for local llama-server completions
│   ├── fs/
│   │   └── FileDiskReader.ts       # Filesystem reader adapter
│   └── cli/
│       └── index.ts                # Commander executable composition root
│
└── shared/                    # Reusable primitives
    ├── errors/
    │   └── DomainError.ts     # Typed domain and infrastructure errors
    └── types/
        └── Result.ts          # Functional Result<T, E> error handling
```

---

## 2. Getting Started

### Installation
```bash
# Strictly managed via PNPM
pnpm install
```

### Build
```bash
# Compile TypeScript to dist/ with strict type safety
pnpm run build
```

### Execution Modes

#### Offline / Deterministic Testing (Mock Engine)
Does not require any local language model or server running:
```bash
pnpm run dev refactor src/domain/entities/SourceFile.ts --mock
```

#### Local Edge Inference (via llama-server)
Requires `llama-server` running with our GGUF model:
```bash
# Default endpoint: http://127.0.0.1:8080
pnpm run dev refactor src/domain/entities/SourceFile.ts

# Custom endpoint and model name
pnpm run dev refactor src/domain/entities/SourceFile.ts --url http://192.168.6.34:8080 --model Qwen3-Coder-30B
```
