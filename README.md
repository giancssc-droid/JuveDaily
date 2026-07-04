# JuveDaily

Automated Juventus news digest powered by RSS and GitHub Actions.

## Overview

JuveDaily collects Juventus-related news from public RSS sources and generates both a web page and RSS feed focused on the latest developments around the club.

The project is designed to provide a fast daily briefing without having to monitor multiple Telegram channels, websites, and news sources.

## Sources

Current source:

- RSSGround feed aggregation
  - GJustJuve
  - PuebloJ
  - JNetwork24
  - Fabrizio Romano references
  - Romeo Agresti references
  - Tuttosport references
  - Additional Juventus-related channels

## Features

- Automatic updates via GitHub Actions
- Last 12 hours filtering
- Duplicate removal
- HTML daily digest
- RSS output
- Direct Telegram links

## Public URLs

Daily Digest:

https://giancssc-droid.github.io/JuveDaily/juventus_daily.html

RSS Feed:

https://giancssc-droid.github.io/JuveDaily/juventus_daily.xml

## Generated Content

The digest may include:

- Transfer market news
- Official announcements
- Club updates
- Contract news
- Juventus Women news
- Media reports
- Telegram source updates

## Automation

GitHub Actions rebuilds the digest automatically.

## Tech Stack

- Python
- FeedParser
- FeedGen
- GitHub Actions
- GitHub Pages

## Purpose

Personal Juventus monitoring system designed to provide a quick overview of the most important developments each day.
