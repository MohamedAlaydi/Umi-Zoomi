# Giving the whole team Amass access

Asked at 12:15 on 14 Nov. Short answer: yes, but not by passing one key
around. There are three routes and the first one takes two minutes.

---

## Route 1. Ask the Amass people on site. Do this first.

The hackathon has an Amass prize (a free month for best use of the
platform), so the organisers already have a relationship with them and
somebody from Amass is reachable today. Ask for **either** hackathon keys
for five people **or** five seats in one organisation.

An organisation is the thing we actually want, because Amass bills credits
at the organisation level while issuing keys per user. That gives everyone
their own key, one shared balance, and one admin who can see what is left.
Nothing else in their documented model gives us all three.

Cost of asking: one conversation. Do it before building anything.

## Route 2. No keys at all: each person adds the connector themselves.

The Amass MCP connector is `https://mcp.amass.tech/mcp` and it is
sign-in-required, so it authenticates per person in their own Claude.
Everyone on the team already has their own Claude login on the VM, so:

1. each person signs up free at amass.tech (the free plan is $0 and takes
   no card)
2. each person adds the Amass connector in their own Claude
3. done, and nobody has touched a credential

This is the right route for literature work, which is most of what we use
Amass for. It needs no key, no shared bill, and no script.

What we could **not** confirm: whether MCP usage is metered against the
same credits as the API. Their connector page does not say. If the free
plan turns out not to cover the MCP server, route 1 is the answer.

## Route 3. One shared API key. Possible. Don't.

The documentation is explicit that keys are scoped to a user, and the rate
limit is **60 requests per 60 seconds keyed by user plus organisation**. So
a single shared key means:

- five people sharing one 60-per-minute budget, and whoever is running a
  loop starves everyone else
- one person's card carrying the whole bill, at $0.05 per 20 search results
- no way to cut off one person without revoking the key for everyone
- nobody except the organisation admin can even check the remaining
  balance: the credits endpoint returns 403 to members

If we do it anyway for an unattended script, it goes in an environment
variable and never in this repo. The repo is public and the pre-commit hook
rejects secret-shaped lines.

---

## The plumbing, which is now in the repo

`scripts/amass` wraps the Platform API the same way the rest of the repo
wraps Foundry: it reads the key from the environment and never stores it.

```bash
amass search biomedcore "trastuzumab Met-107 oxidation"
amass search biomedcore "HER2 epitope competitive binding" 40
amass get biomedcore <amass-id>
amass credits
amass cores
```

Each person sets their own key once. Tell a teammate this and nothing else:

```bash
echo yourname > ~/.team_me     # once, if you have not already
~/team14/scripts/amass key     # paste your key when prompted
. ~/team14/scripts/env.sh
```

**Why not `~/.bashrc`.** We share one Linux user, so there is one
`~/.bashrc` for all five of us and an `export AMASS_API_KEY=` line in it
would be overwritten by whoever edits it next. `amass key` writes
`~/.amass-keys/<yourname>.key` instead, and `scripts/env.sh` reads the one
matching `~/.team_me`. Tested with two names on one account: both keys
survive and each shell gets the right one.

`amass key` reads the key from the terminal without echoing it, so it never
lands in shell history, in a log, or in a chat window. If you are asking
Claude to set this up for you, Claude should run `amass key` and let **you**
paste the key. Do not type a key into a chat.

**The honest limit of this.** The key files are mode 600, but we all share
one Linux account, so that stops accidents, not teammates: anyone on the VM
can read anyone's key. Per-person files solve clobbering, not isolation. If
you want real isolation, use route 2 and never put a key on the VM at all.

`scripts/env.sh` also still picks up `AMASS*` from `~/.bashrc` alongside
`FOUNDRY*`, `QUAY*` and `NXF*`, for anyone running this off the shared VM.
The per-person file wins where both exist.

Every call prints what it cost and how much rate-limit headroom is left, on
stderr, because a 100-result search is $0.25 and that adds up across five
people:

```
# cost 5 credits (1 credit = $0.01) | 54 requests left this minute
```

## The API, as documented

- base URL `https://api.amass.tech/api/v1`
- header `Authorization: Bearer amass_...`
- keys are made at https://platform.amass.tech/api-keys and shown once
- six cores: biomedcore, trialcore, drugcore, regulatorycore, genecore,
  patentcore (preview)
- three endpoints per core, the same shape for all of them: search
  `GET /cores/{core}/records`, fetch `GET /cores/{core}/records/{id}`,
  batch id conversion `POST /cores/{core}/records/lookup`
- no pagination at all: one search returns at most 300 results via `limit`
- pricing: $0.05 per 20 search results, $0.01 per fetch, 1 credit = $0.01
- interactive reference https://platform.amass.tech/api-reference and the
  OpenAPI spec at https://api.amass.tech/api/doc/openapi.json

Checked against platform.amass.tech/documentation (quickstart,
authentication, pricing, overview), amass.tech and the Claude connector
page, 14 Nov 2026. Their own pages disagree about whether the rate limit is
keyed per user or per user plus organisation, so treat 60 per minute as the
number we plan against either way.

**Not documented anywhere we could find**: a student or academic programme,
a hackathon tier, how much API use the free plan includes, and whether MCP
and API usage share a balance. All four are questions for the Amass people
on site, which is why route 1 is first.
