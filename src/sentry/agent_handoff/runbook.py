import html
import re
import shlex

from django.core.cache import cache
from jinja2 import Environment, PackageLoader, StrictUndefined

from sentry.tasks.release_registry import APP_INDEX_CACHE_KEY

# Markdown labels and shell blocks are escaped for their respective contexts below.
_ENVIRONMENT = Environment(
    loader=PackageLoader("sentry", "templates"),
    autoescape=False,
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)

_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+.!|~>-])")
_SHA256_HEX = re.compile(r"[0-9a-f]{64}")
_INSTALLER_URL = "https://cli.sentry.dev/install"


def _escape_label(value: str) -> str:
    """Keep untrusted context on one line, outside Markdown instructions or HTML."""
    single_line = " ".join(value.split())
    printable = "".join(character for character in single_line if character.isprintable())
    return _MARKDOWN_SPECIAL.sub(r"\\\1", html.escape(printable, quote=False))


def _code_block(value: str, language: str = "bash") -> str:
    # Minted codes are opaque; keep even unexpected backticks inside their code block.
    fence = "`" * max(3, max((len(run) + 1 for run in re.findall(r"`+", value)), default=0))
    return f"{fence}{language}\n{value}\n{fence}"


def _installer_sha256() -> str | None:
    """The CLI installer's SHA-256 from the release registry cache, if published.

    The installer is served from cli.sentry.dev; the registry checksum comes from a separate
    trust domain, so tampering with the served script alone fails verification.
    """
    apps = cache.get(APP_INDEX_CACHE_KEY)
    try:
        checksum = apps["sentry"]["files"]["install"]["checksums"]["sha256-hex"]
    except (KeyError, TypeError):
        return None
    if isinstance(checksum, str) and _SHA256_HEX.fullmatch(checksum):
        return checksum
    return None


def _installer_command(environment: str, checksum: str | None) -> str:
    if checksum is None:
        return f"curl -fsSL {_INSTALLER_URL} | {environment} bash"
    return "\n".join(
        [
            'installer="$(mktemp)"',
            f'curl -fsSL {_INSTALLER_URL} -o "$installer"',
            'checksum="$( (sha256sum "$installer" 2>/dev/null || shasum -a 256 "$installer")'
            " | cut -d ' ' -f 1)\"",
            f'if [ "$checksum" = "{checksum}" ]; then',
            f'  {environment} bash "$installer"; status=$?',
            "else",
            '  echo "Installer download or checksum check failed; not running it." >&2; status=1',
            "fi",
            'rm -f "$installer"; (exit "$status")',
        ]
    )


def render_agent_runbook(
    *,
    organization_slug: str,
    organization_name: str,
    user_email: str,
    sentry_url: str,
    client_id: str,
    setup_code: str,
) -> str:
    """Render a private guide from already-authorized context and minted credentials."""
    instance_environment = (
        f"SENTRY_HOST={shlex.quote(sentry_url)} SENTRY_URL={shlex.quote(sentry_url)}"
    )
    setup_environment = (
        f"{instance_environment} SENTRY_CLIENT_ID={shlex.quote(client_id)} "
        f"SENTRY_SETUP_CODE={shlex.quote(setup_code)}"
    )
    auth_status = _code_block(f"{instance_environment} sentry auth status --fresh --json")
    installer_sha256 = _installer_sha256()
    installer = _code_block(_installer_command(setup_environment, installer_sha256))
    bootstrap = _code_block(
        f"{setup_environment} sentry auth bootstrap --url {shlex.quote(sentry_url)}"
    )

    return _ENVIRONMENT.get_template("sentry/agent_handoff/runbook.md").render(
        {
            "sentry_url": _escape_label(sentry_url),
            "user_email": _escape_label(user_email),
            "organization_name": _escape_label(organization_name),
            "organization_slug": _escape_label(organization_slug),
            "auth_status": auth_status,
            "installer": installer,
            "installer_verified": installer_sha256 is not None,
            "bootstrap": bootstrap,
        },
    )


def render_claim_runbook(*, claim_url: str) -> str:
    command = (
        f"curl -sS -X POST {shlex.quote(claim_url)} --data-urlencode 'handoff_code=HANDOFF_CODE'"
    )
    return _ENVIRONMENT.get_template("sentry/agent_handoff/claim.md").render(
        claim_command=_code_block(command),
    )
