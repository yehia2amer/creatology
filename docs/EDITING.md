# Local editing guide

The native Git repository is this `site` directory. Select it, not `public`, `content`, `admin`, the WordPress backup, or the parent migration directory.

1. Run `Start-Editor.cmd` from PowerShell (`.\Start-Editor.cmd`). It uses uv, the pinned Python script dependencies, and Zola 0.23.6. Initial installation needs internet; later builds use local caches.
2. Open http://localhost:1111/admin/ in full Microsoft Edge or Google Chrome.
3. Choose **Work with Local Repository**, select this `site` directory, and allow the browser's folder access prompt. `.git` already exists. The configured `local/ayman-amer` repository is a deliberate local-only identifier; no remote account or login is needed.
4. Open an existing entry, or choose its collection and create one. New entries default to draft. Set its title, date, image, category and unique path, for example `/books/new-book/`. Imported paths are protected during builds.
5. Use the visual Markdown editor for ordinary new content. Keep complex imported tables/embeds in raw mode when necessary; avoid converting their HTML back and forth. Original titles, excerpts and content were preserved, including existing spelling.
6. Save, wait for the terminal's successful build, then refresh http://localhost:1111/. The admin tab stays open. Draft pages are excluded from the visitor build. Turn draft off when intentionally publishing locally.
7. Review the changes in a Git client and commit them. No remote exists yet; saves do not deploy the site. Reload the CMS after changes made by another Git client.

If the repository picker fails in the Codex in-app browser, open the same admin URL in full Edge/Chrome. Use the project root above. No filesystem permission is required for visitors; it is only needed by the local editor. The disposable editor at port 1112 is a test backend and does not edit this repository.

For just a production build, run `.\Build.cmd`. Deployable files are only under `public/`. Never publish the parent migration folder, `.git`, `editorial`, `scripts`, `.tools`, `.local`, source backups or SQL.

The local server binds to 127.0.0.1. Closing its terminal stops preview/editing services. If port 1111 is already in use, close the previous editor terminal before launching another instance.

Arabic quick guide: شغّل Start-Editor.cmd، ثم افتح رابط الإدارة في Edge أو Chrome. اختر Work with Local Repository وحدد مجلد site نفسه. احفظ التغييرات، انتظر نجاح البناء، ثم حدّث صفحة المعاينة. المسودة لا تظهر في الموقع؛ لا تغيّر روابط الصفحات القديمة. الحفظ محلي ولا ينشر الموقع على الإنترنت.

Official workflow: https://sveltiacms.app/en/docs/workflows/local

Imported drafts use private placeholder paths. If intentionally publishing one later, first choose a unique real public path; published legacy page paths remain locked. Homepage composition can be edited directly in its homepage collection independently of standalone event/feature pages.