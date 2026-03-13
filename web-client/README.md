# MarketWatch Web Client

A modern React + TypeScript single-page application (SPA) for the MarketWatch currency watchlist manager.

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router v6** - Client-side routing
- **React Query (TanStack Query)** - Server state management
- **Axios** - HTTP client
- **Vitest + React Testing Library** - Testing

## Prerequisites

- Node.js 18+ 
- npm or yarn

## Installation

```bash
cd web-client
npm install
```

## Configuration

Create a `.env` file (or copy from `.env.example`):

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm test` | Run tests with Vitest |
| `npm run typecheck` | Run TypeScript type checking |

## Features

### Authentication

- **Register**: Create a new account with username, password, and optional email
- **Login**: Authenticate and receive a token (stored in localStorage)
- **Logout**: Clear token and redirect to login page

### Dashboard

- **Add Symbol**: Add currency pairs (e.g., USD/SEK) to your watchlist
- **View Watchlist**: See all tracked currency symbols
- **Remove Symbol**: Delete symbols from your watchlist
- **Update Prices**: Fetch latest exchange rates from Frankfurter API
- **Export CSV**: Download price data as a CSV file

## Project Structure

```
web-client/
├── public/              # Static assets
├── src/
│   ├── __tests__/       # Test files
│   │   ├── auth.test.tsx
│   │   └── dashboard.test.tsx
│   ├── api/             # API client
│   │   └── client.ts
│   ├── auth/            # Authentication context
│   │   └── AuthProvider.tsx
│   ├── layout/          # Layout components
│   │   └── Layout.tsx
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   ├── App.tsx          # Root component with routing
│   ├── config.ts        # Configuration
│   ├── index.css        # Global styles
│   ├── main.tsx         # Entry point
│   └── setupTests.ts    # Test setup
├── index.html
├── package.json
├── tailwind.config.cjs
├── tsconfig.json
└── vite.config.ts
```

## API Integration

The app connects to the FastAPI backend (`final_project.web`). All API calls use token-based authentication:

```typescript
// Token is automatically attached to requests via axios interceptor
Authorization: Bearer <token>
```

### Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/register` | Create account |
| POST | `/login` | Get auth token |
| POST | `/logout` | Invalidate token |
| GET | `/me/watchlist` | List symbols |
| POST | `/me/watchlist` | Add symbol |
| DELETE | `/me/watchlist/{symbol}` | Remove symbol |
| GET | `/me/prices` | Get prices |
| POST | `/me/prices/update` | Refresh prices |
| GET | `/me/prices/export` | Download CSV |

## Testing

Run tests:

```bash
npm test
```

Tests cover:
- Auth context (login, logout, register, localStorage)
- Dashboard (add/remove symbols, update prices, error handling)

## Production Build

```bash
npm run build
```

Output is in the `dist/` directory. You can:

1. Serve it with the FastAPI backend (add static file serving)
2. Deploy to Netlify, Vercel, or any static host
3. Use `npm run preview` to test locally

## Security Notes

- Tokens are stored in localStorage (suitable for demo/MVP)
- For production, consider:
  - Using secure httpOnly cookies
  - Implementing token refresh
  - Adding CSRF protection
  - Using HTTPS

## License

MIT
