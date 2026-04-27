#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def get_info(json_data):
    for key, value in json_data.items():
        if value == "" or value == "N/A":
            json_data[key] = "unknown"
    title = json_data["title"]
    studio = json_data["studio"]
    publisher = json_data["publisher"]
    year = json_data["year"]
    outline = json_data["outline"]
    runtime = json_data["runtime"]
    director = json_data["director"]
    actor_photo = json_data["actor_photo"]
    actor = json_data["actor"]
    release = json_data["release"]
    tag = json_data["tag"]
    number = json_data["number"]
    cover = json_data["cover"]
    website = json_data["website"]
    series = json_data["series"]
    return (
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
    )

