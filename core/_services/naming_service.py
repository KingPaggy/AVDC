"""Naming service for AVDC.

Resolves file/folder naming patterns by substituting metadata placeholders
(e.g. number, title, actor) into config-defined templates.
"""
from core._services.metadata import get_info


def resolve_name(pattern: str, json_data: dict, max_length: int = 100) -> str:
    """Resolve a naming pattern using metadata from json_data.

    Supports placeholders: title, studio, year, runtime, director, actor,
    release, number, series, publisher.

    Truncates to max_length characters by shortening the title portion.
    """
    (
        title,
        studio,
        publisher,
        year,
        outline,
        runtime,
        director,
        actor_photo,
        actor,
        release,
        tag,
        number,
        cover,
        website,
        series,
    ) = get_info(json_data)

    # Actor truncation: if 10+ actors, show first 3 + "等演员"
    actor_parts = actor.split(",")
    if len(actor_parts) >= 10:
        actor = actor_parts[0] + "," + actor_parts[1] + "," + actor_parts[2] + "等演员"

    name = (
        pattern.replace("title", title)
        .replace("studio", studio)
        .replace("year", year)
        .replace("runtime", runtime)
        .replace("director", director)
        .replace("actor", actor)
        .replace("release", release)
        .replace("number", number)
        .replace("series", series)
        .replace("publisher", publisher)
    )

    name = name.replace("//", "/").replace("--", "-").strip("-")

    if len(name) > max_length:
        name = name.replace(title, title[:70])

    return name
