# Native implementation

The theme is original Tera/HTML/CSS/JavaScript under `themes/creatology`, with native Zola Markdown/YAML content and taxonomy assignments. Portio-Zola and Zola Sveltia Source informed the UX; their code was not copied. Existing rich HTML is retained inside editable native content to preserve tables, embeds and source text.

The build runs one shared adapter per concern: `refresh_content.py` refreshes edited/new listings, category membership, pagination and homepage rails; `media.py` maps responsive image sources; Zola renders templates and WebP derivatives; `refresh_feeds.py` preserves unchanged feeds and refreshes edited content feeds. Original media URLs and bytes remain intact. `source-versions.json` and `source-body-versions.json` distinguish source baselines from later editor changes; do not regenerate them casually.

`data/protected-routes.json` guards imported page paths. `data/compatibility.json` records existing redirects/source failures; the local server and supplied SiteGround rules implement it. The form forwards to existing CF7 form 32. There is no database or WordPress frontend runtime in the static output.

`Start-Editor.cmd` uses uv and `dev.py` to build, serve localhost and watch editorial/theme changes. The final runtime has no test-backend route. Migration scripts in the parent directory are historical phase tools: several are one-time patches, not safe general regeneration commands. Use the runtime build for ordinary editing.

All Python entry points are saved scripts with PEP 723 headers and executed with uv. Runtime versions are pinned in headers; Zola/Sveltia provenance is in `docs/dependencies.json`. `Resolve-Python.ps1` prefers an existing supported Python executable, working around this machine's uv minor-version-link installation error. On another computer uv can provision Python 3.12.

On Windows with restricted PowerShell script execution, the recommended .cmd launchers work without changing the execution policy.