---
title: Firefighter Suite API
emoji: 🔥
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 8080
pinned: false
short_description: Backend API for the IE492 Firefighter Web Suite (FastAPI).
---

# Firefighter Suite — Backend API

FastAPI service that ingests an ESA WorldCover bbox, builds a graph from
land-cover + OSM overlays, simulates 8 firefighter strategies, and returns
a topology-based strategy recommendation.

This Space hosts only the backend. The user-facing frontend is on Netlify
and proxies `/api/*` calls to this Space.
