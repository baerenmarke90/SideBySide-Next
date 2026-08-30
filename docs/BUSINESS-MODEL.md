# SideBySide Next – Product and Business Model

## Goal

SideBySide Next is intended to combine two models:

1. technically proficient private users can operate the application themselves;
2. private users who do not want to administer their own server can use the officially operated SideBySide Cloud service.

Cloud monetization is based on operations, convenience, and service — not on artificially degrading the functionality of the Self-Hosted build.

## Operating models

### SideBySide Self-Hosted

SideBySide Self-Hosted is intended for private users who want to install and operate SideBySide Next themselves.

Personal and other noncommercial use is governed by the [PolyForm Noncommercial License 1.0.0](../LICENSE).

Self-Hosted users are responsible in particular for:

- installation and updates;
- server and database operations;
- TLS, domain, and reverse proxy;
- backups and recovery;
- monitoring and availability;
- email and push infrastructure where those functions require external infrastructure;
- storage and operating costs.

Self-Hosted should use the shared Application Core and must not be artificially stripped of Core functionality solely to promote the Cloud. Differences may result from the operating model, for example managed infrastructure, available integrations, storage, or service offerings.

### SideBySide Cloud

SideBySide Cloud is the officially operated Managed Service for users who want to use SideBySide without administering infrastructure themselves.

Users primarily pay for operations and the associated services, for example:

- provisioned and maintained infrastructure;
- automatic updates and migrations;
- backups and recovery processes;
- monitoring and availability;
- security maintenance;
- managed storage;
- email, push, and comparable operational services;
- an immediately usable Web and app experience without self-administered servers.

The Cloud may be offered in different plans, for example based on storage, service scope, or additional managed services. Specific prices and limits will be defined only after cost and market analysis.

## Official apps and clients

Official Web, Android, and potentially additional clients are part of the SideBySide product.

The commercial value of the official Cloud does not come from technically excluding Self-Hosted users from the official clients, but from the convenience of a fully operated service. Where technically and securely appropriate, the official clients should therefore be able to work with both SideBySide Cloud and compatible Self-Hosted instances.

App-store publication, signing, update channels, push infrastructure, and other distribution or platform services provided by the project operator may be tied separately to the official operation where this is required for technical, security, or economic reasons.

## Commercial use by third parties

Publishing the source code does not grant general permission for commercial use.

Third parties require a separate commercial license in particular for:

- a paid SideBySide hosting or SaaS service;
- integration into a commercial product;
- White-Label or OEM offerings;
- commercial redistribution or marketing.

The authoritative project policy is documented in [COMMERCIAL-LICENSE.md](../COMMERCIAL-LICENSE.md).

## Community contributions

Community forks and Pull Requests are explicitly welcome. Changes may be merged into the main branch after review when they fit the project functionally, technically, and strategically.

The Maintainers decide whether to accept a contribution. Contributions are governed by [CONTRIBUTING.md](../CONTRIBUTING.md) and the [Contributor License Agreement](../CLA.md), so accepted Contributions can be reused with legal clarity both in the noncommercial model and under later commercial licensing.

## Development consistency rule

This business model is an active development constraint, not only a commercialization or launch document.

Every human- or AI-assisted development change must review its consistency with this model before implementation and record the result in the pull request. The review may conclude that a change has no business/freemium impact, but that conclusion requires a short rationale.

The review must be revisited before merge if implementation decisions changed any of the following:

- Free/Premium/Mixed/non-paywallable feature classification;
- entitlement or capability boundaries;
- relationship/couple ownership of commercial entitlements;
- Self-Hosted versus SideBySide Cloud/Managed behavior;
- managed storage, compute, rendering, provider/API, inference, email/push, support, or comparable ongoing cost;
- quotas, storage limits, fair-use rules, retention, or other managed-resource behavior;
- trial, grandfathering, downgrade, restore, export, or existing-data semantics.

A change must not silently introduce a business-model contradiction. If a development decision requires changing this model or the authoritative Free/Premium feature matrix, the product decision and documentation change must be explicit and traceable before merge.

Until the detailed freemium/Premium decisions tracked in issue #262 are promoted into authoritative versioned repository documentation, #262 is the current working decision source for those pending feature-tier questions. This temporary reference does not replace the requirement to move finalized decisions into repository documentation.

The concrete implementation and pull-request rules are defined in [`AGENTS.md`](../AGENTS.md).

## Product principles

The business model follows these principles:

- **Self-Hosting remains a real product.** It is not merely a demo for the Cloud.
- **The Cloud sells convenience and operations.** Its added value is a managed service.
- **One shared Application Core.** Cloud and Self-Hosted should not diverge unnecessarily.
- **No artificial degradation.** Core functionality is not removed from Self-Hosted solely for monetization.
- **Commercial use remains controlled.** Third parties require a separate license for it.
- **Community contributions can flow back.** The Maintainers decide whether they are accepted into `main`.
- **Privacy remains a product characteristic.** Monetization must not rely on advertising, selling personal data, or unnecessary tracking.
- **Business-model consistency is checked during development.** Product, entitlement, Cloud/Self-Hosted, managed-resource, and downgrade assumptions must remain traceable as the implementation evolves.

## Positioning

Future communication may explain the model along these lines:

> You can self-host SideBySide Next for personal, noncommercial use. If you do not want to operate your own server, install updates, or manage backups, you can instead use SideBySide Cloud as a fully operated service.

## Not yet defined

This document defines the strategic product structure but deliberately does not yet set final prices, storage limits, SLA commitments, or plan names. Those points will be defined before commercial launch based on actual infrastructure costs, payment fees, app-store costs, support effort, and market positioning.
