from dataclasses import dataclass, field
from typing import Optional
from datetime import date


@dataclass
class Actor:
    name: str
    photo: Optional[str] = None


@dataclass
class Movie:
    title: str = ""
    number: str = ""
    actor: list[str] = field(default_factory=list)
    studio: str = ""
    publisher: str = ""
    director: str = ""
    release: str = ""
    year: str = ""
    runtime: int = 0
    score: str = ""
    outline: str = ""
    cover: str = ""
    cover_small: str = ""
    extrafanart: list[str] = field(default_factory=list)
    tag: list[str] = field(default_factory=list)
    series: str = ""
    actor_photo: dict[str, str] = field(default_factory=dict)
    website: str = ""
    source: str = ""
    imagecut: int = 1

    def is_valid(self) -> bool:
        return bool(self.title and self.title not in ("None", "null"))

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "number": self.number,
            "actor": self.actor,
            "studio": self.studio,
            "publisher": self.publisher,
            "director": self.director,
            "release": self.release,
            "year": self.year,
            "runtime": str(self.runtime) if self.runtime else "",
            "score": self.score,
            "outline": self.outline,
            "cover": self.cover,
            "cover_small": self.cover_small,
            "extrafanart": self.extrafanart,
            "tag": self.tag,
            "series": self.series,
            "actor_photo": self.actor_photo,
            "website": self.website,
            "source": self.source,
            "imagecut": self.imagecut,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Movie":
        actor_str = data.get("actor", "")
        if isinstance(actor_str, str):
            actor = actor_str.strip("[]").replace("'", "").split(",")
            actor = [a.strip() for a in actor if a.strip()]
        else:
            actor = actor_str or []

        tag_str = data.get("tag", "")
        if isinstance(tag_str, str):
            tag = tag_str.strip("[]").replace("'", "").replace(" ", "").split(",")
            tag = [t.strip() for t in tag if t.strip()]
        else:
            tag = tag_str or []

        runtime = data.get("runtime", 0)
        if isinstance(runtime, str):
            runtime = int(runtime) if runtime.isdigit() else 0

        return cls(
            title=data.get("title", ""),
            number=data.get("number", ""),
            actor=actor,
            studio=data.get("studio", ""),
            publisher=data.get("publisher", ""),
            director=data.get("director", ""),
            release=data.get("release", ""),
            year=data.get("year", ""),
            runtime=runtime,
            score=data.get("score", ""),
            outline=data.get("outline", ""),
            cover=data.get("cover", ""),
            cover_small=data.get("cover_small", ""),
            extrafanart=data.get("extrafanart", []),
            tag=tag,
            series=data.get("series", ""),
            actor_photo=data.get("actor_photo", {}),
            website=data.get("website", ""),
            source=data.get("source", ""),
            imagecut=data.get("imagecut", 1),
        )

    @classmethod
    def empty(cls) -> "Movie":
        return cls()


@dataclass
class ScraperResult:
    movie: Movie
    source: str
    success: bool
    error: Optional[str] = None
