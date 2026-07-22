# {{cookiecutter.project_slug}}

{{cookiecutter.description}}

## Installation

```bash
pnpm add {{cookiecutter.project_slug}}
```

## Quick Start

```typescript
import { ApiClient } from '{{cookiecutter.project_slug}}'

const client = new ApiClient({
  baseUrl: 'https://api.example.com',
  credentials: {
    grantType: 'client_credentials',
    clientId: 'your_client_id',
    clientSecret: 'your_client_secret',
  },
})

const data = await client.get('/some-endpoint')
```

## Authentication

The SDK supports four OAuth grant types:

- **client_credentials** — server-to-server authentication
- **password** — username/password authentication
- **session_token** — existing session token
- **refresh_token** — token refresh

Token lifecycle (authenticate → cache → refresh before expiry → fallback to full re-auth) is handled automatically.

## Development

```bash
pnpm install       # Install dependencies
pnpm build         # Build the library
pnpm typecheck     # Run TypeScript type checking
pnpm fmt           # Format code with Prettier
```

## License

MIT
