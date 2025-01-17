# Kubiya Chat UI

A modern chat interface built with Next.js 15, React 18, and TypeScript, featuring Auth0 authentication and a sleek UI powered by Tailwind CSS.

## Features

- 🔐 Secure authentication with Auth0
- 💅 Modern UI with Tailwind CSS
- 🚀 Built on Next.js 15 framework
- 📝 Markdown support for chat messages
- 🎨 Responsive design
- 💻 TypeScript for type safety

## Prerequisites

- Node.js (LTS version recommended)
- npm or yarn package manager

## Getting Started

1. Clone the repository:
```bash
git clone <repository-url>
cd kubiya-chat
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Set up environment variables:
Create a `.env.local` file with your Auth0 configuration:
```
AUTH0_SECRET='your-auth0-secret'
AUTH0_BASE_URL='your-base-url'
AUTH0_ISSUER_BASE_URL='your-auth0-domain'
AUTH0_CLIENT_ID='your-client-id'
AUTH0_CLIENT_SECRET='your-client-secret'
```

4. Run the development server:
```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Tech Stack

- **Framework**: Next.js 15
- **Language**: TypeScript
- **Authentication**: Auth0
- **UI Components**: @assistant-ui/react
- **Styling**: Tailwind CSS
- **Markdown Support**: @assistant-ui/react-markdown

## Project Structure

```
kubiya-chat/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   ├── components/        # Reusable components
│   └── auth/             # Authentication related components
├── public/                # Static assets
├── lib/                   # Utility functions and shared code
└── hooks/                # Custom React hooks
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and confidential.
