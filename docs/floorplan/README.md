# Architecture map

Download [index.html](index.html) with its notices, then open it locally. No server or account is needed. Use **Start here** for the source tour, search for every file or route, and choose **Flows** for connected walkthroughs. On a phone expand More for the summary and the details toggle for opened descriptions; fit-to-view labels may be small, so use search/details or zoom. Pinch gestures and assistive technologies were not qualified.

Legacy Python 2 scripts scrape channel video IDs into SQLite and request OAuth-authorized per-video analytics; two additional files are unfinished drafts, not usable entrypoints.

## Scope

All owned application code at the pinned commit is admitted unchanged. Dependency/launch text files and hidden development metadata are outside the conservative mapping admission and listed in source-review.json; applicable configuration remains RAW freshness-pinned. Scanner routes are heuristic. No application, module import, network integration, OAuth flow, database, containerized application or deployment was exercised. This is documentation acceptance only.

Run `python3 docs/floorplan/check_freshness.py` from the repository root. A failure requires source review and regeneration, never blind rebaselining. Normal and optimized stdlib tests are in tests/test_freshness.py.

## Measured navigation limits

At a 390px viewport, initial fit-to-view graph labels are approximately 6.3px effective font size: the overview is not the reading surface. Every searched file/route opens exact authored prose at 13.5px or larger. More, Start here, every authored tour stop and every flow step were exercised at 1440px and 390px with external URLs blocked and zero runtime errors. Zoom produced a readable in-view graph label in the exercised sequence. Icon-only details/zoom controls may be hard to discover. Physical pinch and assistive technologies remain untested.
