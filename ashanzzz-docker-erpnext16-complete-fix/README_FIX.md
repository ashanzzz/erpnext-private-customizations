# ERPNext16 AIO — complete CI/build fix

Target repository: `ashanzzz/docker`

Observed failing run: `31673770964`

## Root cause addressed

The failing Containerfile installed `ashan_cn_procurement` after `bench init` and then launched:

```sh
bench build --app ashan_cn_procurement
```

That starts another Frappe/Yarn production build. The failing run ended in:

```text
yarn run production --apps ashan_cn_procurement --run-build-command
exit status 143
```

The Ashan app currently exposes ordinary files through `hooks.py` such as:

- `public/js/company_compliance_expiry_page.js`
- `public/js/vehicle_fuel_management.js`
- `public/js/procurement_controller.js`
- `public/css/oil_card_form.css`

It does not need a second full production bundle pass for those direct assets.

Frappe v16 itself maps each installed app's `public` directory to
`sites/assets/<app>`. This fix performs that low-cost mapping explicitly after
the vendored app is installed.

## Changes

1. Removed `bench build --app ashan_cn_procurement`.
2. Kept the custom app baked into the immutable image.
3. Added an explicit static-asset symlink:
   `apps/ashan_cn_procurement/ashan_cn_procurement/public`
   -> `sites/assets/ashan_cn_procurement`.
4. Added a Python import sanity check during image build.
5. Made `sites/apps.txt` insertion idempotent.
6. Changed the custom repository ref from stale `master` to its current
   default branch, `main`.
7. Avoided putting the GitHub token in the clone URL.
8. Captured `.ashan-source-commit` and exposed it as an OCI image label.
9. Simplified build decision behavior: every real workflow run builds.
   Monthly scheduled runs therefore also pick up Ashan app changes even when
   the ERPNext version is unchanged.
10. Prevented the workflow's own version-bump commit from causing a duplicate
    bot push build.
11. Preserved ERPNext v16.32.0 tracking and the existing GHCR tags.
12. Preserved the existing `.dockerignore` exception that includes
    `custom-apps/ashan_cn_procurement`.

## Files to replace

- `.github/workflows/erpnext16-single-container-aio.yml`
- `erpnext16/single-aio/Containerfile`
- `erpnext16/scripts/fetch-ashan-custom-app.sh`
- `erpnext16/.dockerignore`
- `erpnext16/image/apps.json`
- `erpnext16/ERPNEXT_VERSION`

The last three are included as known-good companion files so the fix bundle can
be applied as one coherent set.

## Apply

From the unpacked bundle:

```bash
chmod +x apply-to-existing-repo.sh
./apply-to-existing-repo.sh /path/to/docker
```

Then review:

```bash
git diff
```

Commit and push:

```bash
git add .github/workflows/erpnext16-single-container-aio.yml erpnext16
git commit -m "fix(erpnext16): avoid second frontend build and track Ashan main"
git push
```

## Required GitHub secret

The Docker repository still requires:

```text
ASHAN_REPO_TOKEN
```

It must be able to read `ashanzzz/erpnext-private-customizations`.

No secret value is included in this ZIP.

## Validation included

Run:

```bash
./validate-fix.sh
```

This checks shell syntax, branch consistency, removal of the failing second
build, static-asset linking, Docker build-context inclusion, and key workflow
markers.

A full Docker image build cannot be performed inside this artifact-generation
environment, so the definitive integration validation remains the GitHub
Actions build itself.
