# apt.halos.fi

APT package repository for [HaLOS](https://halos.fi) — served via GitHub Pages at [apt.halos.fi](https://apt.halos.fi).

## Usage

Add the repository to a HaLOS device:

```bash
curl -fsSL https://apt.halos.fi/halos-apt-key.asc | sudo gpg --dearmor -o /usr/share/keyrings/halos.gpg

echo "deb [signed-by=/usr/share/keyrings/halos.gpg] https://apt.halos.fi trixie-stable main" \
  | sudo tee /etc/apt/sources.list.d/halos.list

sudo apt update
```

Available distributions:

| Distribution | Description |
|---|---|
| `trixie-stable` | Debian Trixie, stable releases |
| `trixie-unstable` | Debian Trixie, pre-releases |

## How it works

Packages are published automatically by CI workflows in individual HaLOS repositories. When a repo tagged with the `apt-package` topic creates a GitHub release, it dispatches an event to this repository, which:

1. Downloads `.deb` assets from the release
2. Routes packages to the correct distribution based on filename suffixes
3. Generates APT metadata (Packages, Release files) and signs with GPG
4. Publishes to the `gh-pages` branch, served by GitHub Pages

A daily scheduled rebuild ensures the repository stays consistent.

## Repository structure

- `scripts/` — Build and routing logic (suffix parsing, package routing, metadata generation, index page generation)
- `.github/workflows/update-repo.yml` — Main workflow: discovers packages, downloads, routes, builds metadata, publishes
- `.github/workflows/remove-package.yml` — Manual workflow to remove a package from a distribution

## License

[MIT](LICENSE)
