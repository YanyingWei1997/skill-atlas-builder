# Portability and privacy

## Local-only data flow

The scanner reads only the roots passed through `--root`. The builder reads only the inventory and template paths passed through its arguments. Neither script sends data to a network service.

The generated HTML embeds the inventory so it can be opened without a server. Treat that HTML as a local file: it may contain absolute source paths from your own computer.

## Cross-platform notes

- Use `$HOME` and explicit command-line arguments instead of hardcoded user directories.
- `open` is macOS-specific; use `xdg-open` on Linux or open the file through a browser on Windows.
- The page can display install roots for any environment, but a runtime managed by npm or a plugin manager should be installed through that manager rather than by copying directories.
- The delete command is intentionally macOS-oriented because it moves to `$HOME/.Trash`; adapt it to the platform's recoverable trash mechanism before using it elsewhere.
