<div align="center">

# Leaker-Flow - Open Source Generalist AI Agent

(that acts on your behalf)

![Leaker-Flow Screenshot](frontend/public/banner.png)

Leaker-Flow is a fully open source AI assistant that helps you accomplish real-world tasks with ease. Through natural conversation, Leaker-Flow becomes your digital companion for research, data analysis, and everyday challenges—combining powerful capabilities with an intuitive interface that understands what you need and delivers results.

Leaker-Flow's powerful toolkit includes seamless browser automation to navigate the web and extract data, file management for document creation and editing, web crawling and extended search capabilities, command-line execution for system tasks, website deployment, and integration with various APIs and services. These capabilities work together harmoniously, allowing Leaker-Flow to solve your complex problems and automate workflows through simple conversations!

[![License](https://img.shields.io/badge/License-Apache--2.0-blue)](./license)
[![Discord Follow](https://dcbadge.limes.pink/api/server/Py6pCBUUPw?style=flat)](https://discord.gg/Py6pCBUUPw)
[![GitHub Repo stars](https://img.shields.io/github/stars/leaker-flow/leaker-flow)](https://github.com/leaker-flow/leaker-flow)
[![Issues](https://img.shields.io/github/issues/leaker-flow/leaker-flow)](https://github.com/leaker-flow/leaker-flow/labels/bug)

<!-- Keep these links. Translations will automatically update with the README. -->
[Deutsch](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=de) |
[Español](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=es) |
[français](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=fr) |
[日本語](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=ja) |
[한국어](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=ko) |
[Português](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=pt) |
[Русский](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=ru) |
[中文](https://www.readme-i18n.com/leaker-flow/leaker-flow?lang=zh)

</div>

## Table of Contents

- [Leaker-Flow Architecture](#project-architecture)
  - [Backend API](#backend-api)
  - [Frontend](#frontend)
  - [Agent Docker](#agent-docker)
  - [Supabase Database](#supabase-database)
- [Use Cases](#use-cases)
- [Self-Hosting](#self-hosting)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Project Architecture

![Architecture Diagram](docs/images/diagram.png)

Leaker-Flow consists of four main components:

### Backend API

Python/FastAPI service that handles REST endpoints, thread management, and LLM integration with Anthropic, and others via LiteLLM.

### Frontend

Next.js/React application providing a responsive UI with chat interface, dashboard, etc.

### Agent Docker

Isolated execution environment for every agent - with browser automation, code interpreter, file system access, tool integration, and security features.

### Supabase Database

Handles data persistence with authentication, user management, conversation history, file storage, agent state, analytics, and real-time subscriptions.

## Use Cases

1. **Competitor Analysis** - _"Analyze the market for my next company in the healthcare industry, located in the UK. Give me the major players, their market size, strengths, and weaknesses, and add their website URLs. Once done, generate a PDF report."_

2. **VC List** - _"Give me the list of the most important VC Funds in the United States based on Assets Under Management. Give me website URLs, and if possible an email to reach them out."_

3. **Looking for Candidates** - _"Go on LinkedIn, and find me 10 profiles available - they are not working right now - for a junior software engineer position, who are located in Munich, Germany. They should have at least one bachelor's degree in Computer Science or anything related to it, and 1-year of experience in any field/role."_

4. **Planning Company Trip** - _"Generate me a route plan for my company. We should go to California. We'll be in 8 people. Compose the trip from the departure (Paris, France) to the activities we can do considering that the trip will be 7 days long - departure on the 21st of Apr 2025. Check the weather forecast and temperature for the upcoming days, and based on that, you can plan our activities (outdoor vs indoor)."_

5. **Working on Excel** - _"My company asked me to set up an Excel spreadsheet with all the information about Italian lottery games (Lotto, 10eLotto, and Million Day). Based on that, generate and send me a spreadsheet with all the basic information (public ones)."_

6. **Automate Event Speaker Prospecting** - _"Find 20 AI ethics speakers from Europe who've spoken at conferences in the past year. Scrapes conference sites, cross-references LinkedIn and YouTube, and outputs contact info + talk summaries."_

7. **Summarize and Cross-Reference Scientific Papers** - _"Research and compare scientific papers talking about Alcohol effects on our bodies during the last 5 years. Generate a report about the most important scientific papers talking about the topic I wrote before."_

8. **Research + First Contact Draft** - _"Research my potential customers (B2B) on LinkedIn. They should be in the clean tech industry. Find their websites and their email addresses. After that, based on the company profile, generate a personalized first contact email where I present my company which is offering consulting services to cleantech companies to maximize their profits and reduce their costs."_

9. **SEO Analysis** - _"Based on my website, generate an SEO report analysis, find top-ranking pages by keyword clusters, and identify topics I'm missing."_

10. **Generate a Personal Trip** - _"Generate a personal trip to London, with departure from Bangkok on the 1st of May. The trip will last 10 days. Find an accommodation in the center of London, with a rating on Google reviews of at least 4.5. Find me interesting outdoor activities to do during the journey. Generate a detailed itinerary plan."_

11. **Recently Funded Startups** - _"Go on Crunchbase, Dealroom, and TechCrunch, filter by Series A funding rounds in the SaaS Finance Space, and build a report with company data, founders, and contact info for outbound sales."_

12. **Scrape Forum Discussions** - _"I need to find the best beauty centers in Rome, but I want to find them by using open forums that speak about this topic. Go on Google, and scrape the forums by looking for beauty center discussions located in Rome. Then generate a list of 5 beauty centers with the best comments about them."_

## Self-Hosting

Leaker-Flow can be self-hosted on your own infrastructure using our comprehensive setup wizard. For a complete guide to self-hosting Leaker-Flow, please refer to our [Self-Hosting Guide](./docs/SELF-HOSTING.md).

The setup process includes:

- Setting up a Supabase project for database and authentication
- Configuring Redis for caching and session management
- Setting up Daytona for secure agent execution
- Integrating with LLM providers (Anthropic, OpenAI, OpenRouter, etc.)
- Configuring web search and scraping capabilities (Tavily, Firecrawl)
- Setting up QStash for background job processing and workflows
- Configuring webhook handling for automated tasks
- Optional integrations (RapidAPI, Smithery for custom agents)

### Quick Start

1. **Clone the repository**:

```bash
git clone https://github.com/leaker-flow/leaker-flow.git
cd leaker-flow
```

2. **Run the setup wizard**:

```bash
python setup.py
```

The wizard will guide you through 14 steps with progress saving, so you can resume if interrupted.

3. **Start or stop the containers**:

```bash
python start.py
```

### Manual Setup

See the [Self-Hosting Guide](./docs/SELF-HOSTING.md) for detailed manual setup instructions.

The wizard will guide you through all necessary steps to get your Leaker-Flow instance up and running. For detailed instructions, troubleshooting tips, and advanced configuration options, see the [Self-Hosting Guide](./docs/SELF-HOSTING.md).

## Contributing

We welcome contributions from the community! Please see our [Contributing Guide](./CONTRIBUTING.md) for more details.

## Acknowledgements

### Main Contributors

- [Adam Cohen Hillel](https://x.com/adamcohenhillel)
- [Dat-lequoc](https://x.com/datlqqq)
- [Marko Kraemer](https://twitter.com/markokraemer)

### Technologies

- [Daytona](https://daytona.io/) - Secure agent execution environment
- [Supabase](https://supabase.com/) - Database and authentication
- [Playwright](https://playwright.dev/) - Browser automation
- [OpenAI](https://openai.com/) - LLM provider
- [Anthropic](https://www.anthropic.com/) - LLM provider
- [Tavily](https://tavily.com/) - Search capabilities
- [Firecrawl](https://firecrawl.dev/) - Web scraping capabilities
- [QStash](https://upstash.com/qstash) - Background job processing and workflows
- [RapidAPI](https://rapidapi.com/) - API services
- [Smithery](https://smithery.ai/) - Custom agent development

## License

Leaker-Flow is licensed under the Apache License, Version 2.0. See [LICENSE](./LICENSE) for the full license text.
