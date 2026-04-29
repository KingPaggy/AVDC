"""Core application services for AVDC.

Modules are organized into subpackages:
  _config/    — AppConfig, logging, errors, settings
  _models/    — Movie, Actor, ProcessResult
  _scraper/   — ScraperBase, dispatcher, pipeline, adapter
  _services/  — CoreEngine, metadata, naming, emby_client
  _files/     — file_utils, file_operations
  _media/     — image_processing
  _net/       — networking
  _event/     — EventBus, Event, EventType
  scrapers/   — site scraper implementations
"""
