"""
Import/Export Function Keywords for grandMA2 Command Builder

Handles export of show objects to disk and import from disk into the show.

Live-validated on grandMA2 onPC 3.9.60.65. Key findings:
- /path= is omitted intentionally: Windows paths with spaces in "MA Lighting
  Technologies" break MA2 command parsing, and the MA2 internal path
  (/data/ma/actual/gma2/...) fails for imports. Default routing is reliable.
- Import requires a destination (At ObjectType N); omitting it gives Error #28.
- MA2 routes files to type-specific subfolders automatically:
    macros/, effects/, plugins/, matricks/, masks/ — or importexport/ (default)

Fixture type import (EditSetup/FixtureTypes context):
- Key format: "manufacturer@fixture@mode"  e.g. "Martin@Mac700Profile_Extended@Extended"
- Must be sent while in EditSetup/FixtureTypes context (via ChangeDest navigation)

Fixture layer import (EditSetup/Layers context):
- File must exist in importexport/ directory
- Must be sent while in EditSetup/Layers context (via ChangeDest navigation)

Content provenance & manifest builders:
- build_provenance_comment: XML comment with creator, source, license, tool metadata
- build_content_manifest: JSON manifest for marketplace content bundles

Included functions:
- export_object: Build an Export command
- import_object: Build an Import command
- import_fixture_type_cmd: Build Import command for a library fixture type (EditSetup/FixtureTypes context)
- import_layer_cmd: Build Import command for a fixture layer XML file (EditSetup/Layers context)
- build_provenance_comment: Build XML comment with content provenance metadata
- build_content_manifest: Build JSON manifest for marketplace content bundles
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ..constants import CONTENT_LICENSES, CONTENT_SOURCES, CONTENT_TIERS

# Object types that can be exported (validated live on MA2 3.9.60.65)
EXPORT_OBJECT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "channel", "screen", "filter",
}

# Object types that can be imported (Screen excluded — Error #16 RESIZE FORBIDDEN)
IMPORT_OBJECT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "filter",
}

# Type-specific subfolders (informational, used in docstrings/tool descriptions)
# MA2 routes automatically — these are shown in MA2 feedback messages
IMPORT_EXPORT_SUBFOLDERS = {
    "macro": "macros/",
    "effect": "effects/",
    "plugin": "plugins/",
    "matricks": "matricks/",
    "mask": "masks/",
    # all others → importexport/
}


def export_object(
    object_type: str,
    object_id: str | int | None = None,
    filename: str | None = None,
    *,
    overwrite: bool = False,
    noconfirm: bool = False,
    style: str | None = None,
) -> str:
    """
    Construct an Export command.

    MA2 syntax: Export [ObjectType] [ID] ["filename"] [/flags]

    Args:
        object_type: Object type keyword (e.g. "Group", "Preset", "Macro")
        object_id: ID, range ("1 thru 5"), preset ref ("1.3"), or None for all
        filename: Output filename without extension or path
        overwrite: Add /overwrite flag
        noconfirm: Add /noconfirm flag
        style: "csv" or "html" (default: xml)

    Returns:
        str: MA2 export command string

    Examples:
        >>> export_object("Group", 1, "mygroups")
        'export Group 1 "mygroups"'
        >>> export_object("Macro", "1 thru 5", "macros", overwrite=True)
        'export Macro 1 thru 5 "macros" /overwrite'
        >>> export_object("Preset", "1.3", "dimmer3", noconfirm=True)
        'export Preset 1.3 "dimmer3" /noconfirm'
        >>> export_object("Sequence", 2, "seq2", style="csv")
        'export Sequence 2 "seq2" /style=csv'
    """
    parts = ["export", object_type]
    if object_id is not None:
        parts.append(str(object_id))
    if filename is not None:
        parts.append(f'"{filename}"')

    options = []
    if overwrite:
        options.append("/overwrite")
    if noconfirm:
        options.append("/noconfirm")
    if style is not None:
        options.append(f"/style={style}")
    if options:
        parts.extend(options)

    return " ".join(parts)


def import_object(
    filename: str,
    destination_type: str,
    destination_id: str | int | None = None,
    *,
    noconfirm: bool = False,
    quiet: bool = False,
) -> str:
    """
    Construct an Import command.

    MA2 syntax: Import "filename" At ObjectType [N] [/flags]

    Destination is required — MA2 returns Error #28 (NO CUE SOURCE GIVEN)
    without it. MA2 routes the file lookup to the correct type-specific
    subfolder automatically.

    Args:
        filename: Source filename without extension or path
        destination_type: Object type keyword (e.g. "Group", "Macro")
        destination_id: Slot number or preset ref ("T.N"). None = next free slot
        noconfirm: Add /noconfirm flag
        quiet: Add /quiet flag (suppress output messages)

    Returns:
        str: MA2 import command string

    Examples:
        >>> import_object("mygroups", "Group", 5)
        'import "mygroups" at Group 5'
        >>> import_object("macros", "Macro")
        'import "macros" at Macro'
        >>> import_object("preset_dimmer", "Preset", "1.99", noconfirm=True)
        'import "preset_dimmer" at Preset 1.99 /noconfirm'
        >>> import_object("show_backup", "Group", 10, quiet=True)
        'import "show_backup" at Group 10 /quiet'
    """
    parts = ["import", f'"{filename}"', "at", destination_type]
    if destination_id is not None:
        parts.append(str(destination_id))

    options = []
    if noconfirm:
        options.append("/noconfirm")
    if quiet:
        options.append("/quiet")
    if options:
        parts.extend(options)

    return " ".join(parts)


def import_fixture_type_cmd(manufacturer: str, fixture: str, mode: str) -> str:
    """
    Build the Import command for a library fixture type.

    Must be sent while in EditSetup/FixtureTypes context (via ChangeDest navigation).
    MA2 key format: 'manufacturer@fixture@mode'

    Args:
        manufacturer: Manufacturer name as it appears in MA2 library (e.g. "Martin")
        fixture: Fixture model name (e.g. "Mac700Profile_Extended")
        mode: Mode string (e.g. "Extended", "Standard")

    Returns:
        str: MA2 import command string for the fixture type

    Examples:
        >>> import_fixture_type_cmd("Martin", "Mac700Profile_Extended", "Extended")
        'Import "Martin@Mac700Profile_Extended@Extended"'
        >>> import_fixture_type_cmd("Generic", "Dimmer", "Mode 1")
        'Import "Generic@Dimmer@Mode 1"'
    """
    return f'Import "{manufacturer}@{fixture}@{mode}"'


def import_layer_cmd(filename: str, layer_index: int | None = None) -> str:
    """
    Build the Import command for a fixture layer XML file.

    Must be sent while in EditSetup/Layers context (via ChangeDest navigation).
    The file must exist in the MA2 importexport directory.

    Args:
        filename: Layer XML filename without extension or path
        layer_index: Target layer slot. None = MA2 picks next free slot

    Returns:
        str: MA2 import command string for the layer file

    Examples:
        >>> import_layer_cmd("dimmers")
        'Import "dimmers"'
        >>> import_layer_cmd("mac700s", 2)
        'Import "mac700s" At 2'
        >>> import_layer_cmd("my_fixtures", 1)
        'Import "my_fixtures" At 1'
    """
    parts = ["Import", f'"{filename}"']
    if layer_index is not None:
        parts.extend(["At", str(layer_index)])
    return " ".join(parts)


def build_provenance_comment(
    *,
    creator: str = "emblem-projects",
    source: str = "ai-assisted",
    license: str = "apache-2.0",
    tool: str = "ma2-onPC-MCP",
    human_contribution: str = "",
    version: str = "1.0.0",
) -> str:
    """Build an XML comment block with content provenance metadata.

    Embedded as ``<!-- ... -->`` so grandMA2 ignores it on import.
    This ensures backward compatibility while carrying licensing,
    attribution, and copyright-relevant metadata with the content.

    Args:
        creator: Content creator identifier (e.g. "emblem-projects").
        source: Content source classification. Must be a key in
                ``CONTENT_SOURCES`` ("human", "ai-assisted", "ai-generated").
        license: License identifier. Must be a key in ``CONTENT_LICENSES``.
        tool: Tool/system that generated the content.
        human_contribution: Description of human creative contribution
                           (strengthens copyright claim for ai-assisted content).
        version: Content version string.

    Raises:
        ValueError: If *creator* is empty, *source* is not in CONTENT_SOURCES,
                    or *license* is not in CONTENT_LICENSES.

    Returns:
        str: Multi-line XML comment with provenance fields.

    Examples:
        >>> c = build_provenance_comment(creator="acme", source="human", license="apache-2.0")
        >>> c.startswith("<!-- emblem:provenance")
        True
        >>> "-->" in c
        True
    """
    if not creator or not creator.strip():
        raise ValueError("creator must not be empty")
    if source not in CONTENT_SOURCES:
        raise ValueError(
            f"Invalid source '{source}'. "
            f"Valid sources: {', '.join(CONTENT_SOURCES)}"
        )
    if license not in CONTENT_LICENSES:
        raise ValueError(
            f"Invalid license '{license}'. "
            f"Valid licenses: {', '.join(CONTENT_LICENSES)}"
        )
    # Prevent XML comment injection via field values
    for field_name, field_val in [
        ("creator", creator),
        ("human_contribution", human_contribution),
        ("tool", tool),
        ("version", version),
    ]:
        if "-->" in field_val:
            raise ValueError(
                f"{field_name} must not contain '-->'"
            )

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "<!-- emblem:provenance",
        f"  creator: {creator}",
        f"  source: {source}",
        f"  license: {license}",
        f"  tool: {tool}/{version}",
    ]
    if human_contribution:
        lines.append(f"  human_contribution: {human_contribution}")
    lines.append(f"  generated: {now}")
    lines.append("-->")
    return "\n".join(lines)


def build_content_manifest(
    *,
    name: str,
    description: str,
    version: str = "1.0.0",
    creator: str = "emblem-projects",
    license: str = "apache-2.0",
    tier: str = "premium",
    price_eur: float | None = None,
    console: str = "grandMA2",
    console_version: str = "3.9.60",
    contents: list[dict[str, str]],
    dependencies: list[str] | None = None,
    human_contribution: str = "",
    source: str = "ai-assisted",
) -> str:
    """Build a content bundle manifest (JSON) for marketplace distribution.

    The manifest describes a downloadable content package — its contents,
    licensing, pricing, and compatibility metadata. It travels alongside
    the XML files in a content bundle directory.

    Args:
        name: Bundle name (e.g. "concert-filter-library").
        description: One-line description of the bundle.
        version: Bundle version (semver).
        creator: Content creator identifier.
        license: License key from ``CONTENT_LICENSES``.
        tier: Marketplace tier from ``CONTENT_TIERS``.
        price_eur: Price in EUR. Required when tier is "premium",
                   forbidden when tier is "free".
        console: Target console platform.
        console_version: Minimum console firmware version.
        contents: List of dicts, each with "type", "file", and
                  optionally "slot_range" (e.g. ``{"type": "filter",
                  "file": "filter_003.xml", "slot_range": "3-170"}``).
        dependencies: Optional list of fixture types or other requirements.
        human_contribution: Description of human creative contribution.
        source: Content source classification from ``CONTENT_SOURCES``.

    Raises:
        ValueError: If validation fails (empty name/contents, invalid
                    tier/license/source, missing or forbidden price).

    Returns:
        str: Pretty-printed JSON manifest string.

    Examples:
        >>> m = build_content_manifest(
        ...     name="demo", description="Demo bundle",
        ...     contents=[{"type": "filter", "file": "f.xml"}],
        ...     price_eur=10.0,
        ... )
        >>> import json; d = json.loads(m); d["name"]
        'demo'
    """
    if not name or not name.strip():
        raise ValueError("name must not be empty")
    if not description or not description.strip():
        raise ValueError("description must not be empty")
    if not contents:
        raise ValueError("contents must not be empty")
    if tier not in CONTENT_TIERS:
        raise ValueError(
            f"Invalid tier '{tier}'. "
            f"Valid tiers: {', '.join(CONTENT_TIERS)}"
        )
    if license not in CONTENT_LICENSES:
        raise ValueError(
            f"Invalid license '{license}'. "
            f"Valid licenses: {', '.join(CONTENT_LICENSES)}"
        )
    if source not in CONTENT_SOURCES:
        raise ValueError(
            f"Invalid source '{source}'. "
            f"Valid sources: {', '.join(CONTENT_SOURCES)}"
        )
    if tier == "premium" and price_eur is None:
        raise ValueError("price_eur is required for premium tier")
    if tier == "free" and price_eur is not None:
        raise ValueError("price_eur is not allowed for free tier")

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = {
        "schema": "emblem-content-manifest/1.0",
        "name": name,
        "description": description,
        "version": version,
        "creator": creator,
        "license": license,
        "tier": tier,
        "source": source,
        "console": console,
        "console_version": console_version,
        "contents": contents,
        "generated": now,
    }
    if price_eur is not None:
        manifest["price_eur"] = price_eur
    if dependencies:
        manifest["dependencies"] = dependencies
    if human_contribution:
        manifest["human_contribution"] = human_contribution

    return json.dumps(manifest, indent=2)
