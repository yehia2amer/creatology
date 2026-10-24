# Git and hosting handover

No remote repository, hosting account, production files, DNS or mail settings were changed. Finish and approve the release gates in the migration handover before switching traffic.

## Git

The local repository is initialized on `main`. Review `git status` and `git diff --no-index /dev/null <file>` or use GitHub Desktop's file review for this initial uncommitted import. Add an initial commit after review, create your chosen remote repository, add its URL as `origin`, and push `main`. Do not use the illustrative local CMS identifier as a real remote URL.

Track `content`, `data` baseline files, `editorial` source records, `themes`, `static/admin`, original uploads, scripts and docs. `.gitignore` excludes output, tools, local reports, generated responsive images, search data and runtime listings. The `editorial` directory contains only sanitized source records; WordPress database, mail configuration and credentials are outside this repository.

Once a real repository is chosen, update `static/admin/config.yml` backend `repo` and branch. Local editing still needs no hosted admin service. Remote browser editing is optional and needs separate Git authentication configuration; it has not been connected.

## Keep SiteGround first

This is the prepared compatibility path: build locally, upload **only `public/`**, and merge `docs/siteground-compatibility.htaccess` before the current WordPress rewrite block. First back up the existing public root and `.htaccess`, and use a staging directory/site. Do not overwrite server rules blindly.

Keep WordPress/Contact Form 7 available for `/wp-json/contact-form-7/v1/contact-forms/32/feedback`, including any configured spam protection, and keep existing SiteGround email. The visitor pages are static, but this deliberately retained delivery endpoint is server-side. Do not delete the WordPress runtime until a replacement form delivery service has been chosen and verified. Moving static files to another origin needs explicit CORS/proxy verification; the local preview uses a fixed-origin proxy only for localhost.

Test all paths and redirects, Arabic encoding, feed MIME, query routes, downloads, correct status codes, and form delivery in staging before switching traffic. One labelled delivery test remains unperformed because the user declined sending email. Roll back by restoring the previous document root and `.htaccess`; no SQL conversion is needed.

## Optional free static hosting later

Cloudflare Pages is a plausible next target for static files: its documented Free limits are 20,000 files and 25 MiB per file. Check the actual current release manifest before deployment. The current archive fits those file-count and individual-file constraints, but it is large because original media remain byte-identical.

A plain upload is insufficient for this migration's strict URL contract. Apache `.htaccess` does not execute on Pages. Port the 424 compatibility records to platform routing, including query-specific WordPress routes, preserved 404s and RSS MIME. Query-dependent behavior may require a Pages Function/Worker rather than a static `_redirects` file. Also arrange the existing SiteGround form endpoint's cross-origin delivery. These hosting adapters are intentionally not represented as deployed or verified.

GitHub Pages is another static hosting candidate, but does not execute PHP or Apache rules and cannot directly reproduce query-based server routing. It likewise needs a compatibility layer before it can satisfy this project's release gates. Do not advertise a host migration as parity complete based only on HTML looking correct.

Official references (checked 24 October 2026):
- https://developers.cloudflare.com/pages/platform/limits/
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- https://sveltiacms.app/en/docs/workflows/local
