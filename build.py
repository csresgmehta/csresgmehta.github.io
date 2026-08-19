"""
Static site generator for the Mehta & Mehta CSR Advisory website.

Reads the original Flask project at SOURCE (read-only — never writes there)
and renders every public page to plain HTML files here, ready for GitHub
Pages. Re-run this script any time the content in the original project
changes, to regenerate this folder.

Dropped from the static build (need a live server/DB, can't run on GitHub
Pages): the /admin panel and the contact form's submit-to-database action.
The Webinar page's video listing is re-implemented as client-side JS that
calls the YouTube Data API directly from the visitor's browser (see the
NOTE about the exposed API key below).
"""

import os
import re
import shutil
import sys
from pathlib import Path

SOURCE = Path(r"d:\Projects\csr-website")
# The actual deployable website. Kept in its own "docs" subfolder — separate
# from this generator script — so GitHub Pages can be pointed at it directly
# (repo Settings -> Pages -> Deploy from branch -> main -> /docs) and the
# published site never contains this .py file.
OUTPUT = Path(r"d:\Projects\csr-website-static\docs")

sys.path.insert(0, str(SOURCE))
os.chdir(SOURCE)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(SOURCE / ".env")

from app import app  # noqa: E402
from flask import render_template_string  # noqa: E402
from blog_data import POSTS  # noqa: E402
from data import CATEGORIES  # noqa: E402

client = app.test_client()


# ============================================================
# HELPERS
# ============================================================

def fetch(path):
    resp = client.get(path)
    if resp.status_code >= 400:
        raise RuntimeError(f"{path} returned HTTP {resp.status_code}")
    return resp.data.decode("utf-8")


def depth_of(out_rel_path):
    parts = Path(out_rel_path).parts
    return len(parts) - 1


def rewrite_links(html, depth):
    prefix = "../" * depth

    def repl(match):
        attr, path = match.group(1), match.group(2)
        if path.startswith("/static/"):
            return f'{attr}="{prefix}{path[1:]}"'
        if path == "/":
            return f'{attr}="{prefix}index.html"'
        if path.startswith("/"):
            inner = path[1:]
            if not inner.endswith("/"):
                inner += "/"
            return f'{attr}="{prefix}{inner}index.html"'
        return match.group(0)

    return re.sub(r'(href|src)="(/[^"]*)"', repl, html)


def write_page(out_rel_path, html):
    depth = depth_of(out_rel_path)
    html = rewrite_links(html, depth)
    full_path = OUTPUT / out_rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(html, encoding="utf-8")
    print("  wrote", out_rel_path)


# ============================================================
# 1. RESET OUTPUT (the docs/ folder is 100% generated content)
# ============================================================

print("Cleaning previous build output...")
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir(parents=True)

# ============================================================
# 2. COPY STATIC ASSETS (css / js / img) — byte-identical
# ============================================================

print("Copying static assets...")
shutil.copytree(SOURCE / "static", OUTPUT / "static")

# Browsers request /favicon.ico at the site root regardless of any
# <link rel="icon"> tags, so it needs a copy there too, not just under
# /static/.
shutil.copy(SOURCE / "static" / "favicon.ico", OUTPUT / "favicon.ico")

# ============================================================
# 3. STANDARD PAGES (rendered via the real Flask routes)
# ============================================================

print("Generating pages...")

write_page("index.html", fetch("/"))
write_page("about-us/index.html", fetch("/about-us/"))
write_page("csr-services/index.html", fetch("/csr-services/"))
write_page("csr-services/csr-advisory/index.html", fetch("/csr-services/csr-advisory/"))
write_page("csr-services/esg-brsr-advisory/index.html", fetch("/csr-services/esg-brsr-advisory/"))
write_page(
    "csr-services/social-stock-exchange-advisory/index.html",
    fetch("/csr-services/social-stock-exchange-advisory/"),
)
write_page("our-team/index.html", fetch("/our-team/"))
write_page("blog/index.html", fetch("/blog/"))

for post in POSTS:
    write_page(f"blog/{post['slug']}/index.html", fetch(f"/blog/{post['slug']}/"))

for cat in CATEGORIES:
    write_page(f"category/{cat.lower()}/index.html", fetch(f"/category/{cat.lower()}/"))

# 404 page (GitHub Pages convention: 404.html at the site root)
with app.test_client() as c:
    resp = c.get("/this-page-does-not-exist-404-probe")
    write_page("404.html", resp.data.decode("utf-8"))

# ============================================================
# 4. CONTACT PAGE — custom: no submit-to-DB form, mailto CTA instead
# ============================================================

print("Generating custom Contact page (no backend form)...")

from data import COMPANY, BRANCH_OFFICE_CITIES, OFFICES  # noqa: E402

CONTACT_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Contact Us — {{ company.name }}{% endblock %}

{% block content %}

<section class="page-hero">
  <div class="container">
    <h1>Contact Us</h1>
    <p class="hero-lead">&ldquo;Please Contact Us So We Can Help You&rdquo;</p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="map-embed">
      <iframe
        src="https://www.google.com/maps?q={{ company.head_office | urlencode }}&output=embed"
        loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Mehta &amp; Mehta office location">
      </iframe>
    </div>

    <div class="two-col">
      <div class="card contact-icons">
        <h2 class="section-title">Contact Us</h2>
        <div class="contact-icon-row">
          <span class="contact-icon-circle">\U0001F4DE</span>
          <div>
            <h4>Office Phone</h4>
            <p>Mumbai: {{ company.phone_primary }} / {{ company.phone_secondary.split(' ')[-1] }}</p>
          </div>
        </div>
        <div class="contact-icon-row">
          <span class="contact-icon-circle">\u2709\uFE0F</span>
          <div>
            <h4>Mail Us</h4>
            <p>
              <a href="mailto:{{ company.email }}">{{ company.email }}</a><br>
              <a href="mailto:{{ company.email_secondary }}">{{ company.email_secondary }}</a>
            </p>
          </div>
        </div>
        <div class="contact-icon-row">
          <span class="contact-icon-circle">\U0001F310</span>
          <div>
            <h4>Mehta and Mehta Legal and Advisory Services</h4>
            <p>
              <a href="{{ company.linkedin }}" target="_blank" rel="noopener">LinkedIn</a> &nbsp;|&nbsp;
              <a href="{{ company.youtube }}" target="_blank" rel="noopener">YouTube</a>
            </p>
          </div>
        </div>

        <h3 style="margin-top:28px;">Address</h3>
        {% for office in offices %}
        <p><strong>{{ office.city }}:</strong> {{ office.address }}</p>
        {% endfor %}
      </div>

      <div class="card contact-icons">
        <h2 class="section-title center">Get In Touch</h2>
        <p class="center-text">Have a question about CSR, ESG, or BRSR compliance? Email us directly and our team will get back to you shortly.</p>
        <div class="center-text" style="margin-top:20px;">
          <a class="btn btn-dark" href="mailto:{{ company.email }}">Email Us</a>
        </div>
        <p class="center-text" style="margin-top:16px;color:var(--muted);">
          Or call us at <a href="tel:{{ company.phone_primary }}">{{ company.phone_primary }}</a>
        </p>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt">
  <div class="container center-text">
    <span class="eyebrow" style="justify-content:center;">Across India</span>
    <h2 class="section-title center">Branch Offices</h2>
    <div class="office-grid">
      {% for city in branch_offices %}
      <div class="office-card">
        <h4>\U0001F4CD {{ city }}</h4>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

{% endblock %}
"""

with app.test_request_context("/contact-us/"):
    contact_html = render_template_string(
        CONTACT_TEMPLATE,
        offices=OFFICES,
        branch_offices=BRANCH_OFFICE_CITIES,
    )
write_page("contact-us/index.html", contact_html)

# ============================================================
# 5. WEBINAR PAGE — custom: client-side YouTube fetch (no server)
# ============================================================

print("Generating custom Webinar page (client-side YouTube fetch)...")

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not YOUTUBE_API_KEY:
    print("  WARNING: YOUTUBE_API_KEY not found in .env — webinar page will not load videos.")

WEBINAR_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Webinars — {{ company.name }}{% endblock %}

{% block content %}

<section class="page-hero">
  <div class="container">
    <h1>Webinar</h1>
    <p class="hero-lead">&ldquo;Knowledge sharing session from Mehta &amp; Mehta&rdquo;</p>
  </div>
</section>

<section class="section" style="padding-bottom:0;">
  <div class="container center-text">
    <span class="eyebrow" style="justify-content:center;">Mehta &amp; Mehta YouTube Channel</span>
    <h2 class="section-title center">Knowledge Sharing Sessions</h2>
    <p>Watch our webinars on CSR, ESG, the Social Stock Exchange, and NGO compliance.
      New sessions are added regularly — subscribe to our channel to stay updated.</p>
    <a class="btn btn-primary" href="{{ company.youtube }}" target="_blank" rel="noopener">Subscribe on YouTube</a>
  </div>
</section>

<section class="section" style="padding-top:0;">
  <div class="container">
    <div class="webinar-filter-bar">
      <form class="search-box" id="webinar-search-form">
        <input type="search" id="webinar-search-input" placeholder="Search webinars…" aria-label="Search webinars">
        <button type="submit" class="search-btn" aria-label="Search">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="7" cy="7" r="5.3"/><path d="M11 11L14.5 14.5" stroke-linecap="round"/></svg>
        </button>
      </form>
      <div class="webinar-tabs" id="webinar-tabs">
        <a href="#" class="tab-link active" data-cat="">All</a>
        <a href="#" class="tab-link" data-cat="csr">CSR</a>
        <a href="#" class="tab-link" data-cat="esg">ESG &amp; BRSR</a>
        <a href="#" class="tab-link" data-cat="sse">Social Stock Exchange</a>
      </div>
    </div>

    <p id="webinar-status" class="center-text" style="margin:20px 0;">Loading webinars…</p>
    <div class="card-grid webinar-grid" id="webinar-grid"></div>
  </div>
</section>

<section class="cta-band">
  <div class="container cta-inner">
    <h2>Want us to cover a topic in our next webinar?</h2>
    <a class="btn btn-primary" href="{{ url_for('contact') }}">Suggest a Topic</a>
  </div>
</section>

<script>
(function () {
  var YOUTUBE_API_KEY = "%%YOUTUBE_API_KEY%%";
  var CHANNEL_ID = "UCFiho8xrHI4d8hcQgPQEnPQ";
  var MAX_FALLBACK_VIDEOS = 300;

  var PLAYLISTS = {
    csr: [{ label: "CSR Podcast", id: "PL3JD7VBefrjsUYPgzosEd5SdcEIH778zp" }],
    esg: [
      { label: "ESG series", id: "PL3JD7VBefrjuhV_xt3d2aV2SRJEoTF0N9" },
      { label: "BRSR", id: "PL3JD7VBefrjv00iOO5FRnsfqDG_hGr3Y7" }
    ],
    sse: [{ label: "Social Stock Exchange", id: "PL3JD7VBefrjtaUlP5TipfqHQwi89IDMK4" }]
  };

  // Fallback classification for videos not in any of the playlists
  // above — checked in this order, first match wins, title only.
  var CATEGORY_KEYWORDS = [
    ["sse", ["social stock exchange"]],
    ["esg", ["esg", "brsr"]],
    ["csr", ["csr", "corporate social responsibility", "section 135", "sec 135", "schedule vii"]]
  ];

  var allVideos = [];
  var currentCat = "";
  var currentQuery = "";

  function classifyByKeyword(title) {
    var text = (title || "").toLowerCase();
    for (var i = 0; i < CATEGORY_KEYWORDS.length; i++) {
      var keywords = CATEGORY_KEYWORDS[i][1];
      for (var j = 0; j < keywords.length; j++) {
        if (text.indexOf(keywords[j]) !== -1) return CATEGORY_KEYWORDS[i][0];
      }
    }
    return null;
  }

  function fetchJson(url) {
    return fetch(url).then(function (r) { return r.json(); });
  }

  function fetchPlaylist(playlistId) {
    var url = "https://www.googleapis.com/youtube/v3/playlistItems"
      + "?part=snippet&maxResults=50&playlistId=" + playlistId
      + "&key=" + YOUTUBE_API_KEY;
    return fetchJson(url);
  }

  function buildVideo(sn, vid, cat) {
    var thumbs = sn.thumbnails || {};
    var thumb = (thumbs.high || thumbs.medium || thumbs.default || {}).url || "";
    return {
      id: vid,
      title: sn.title || "",
      date: (sn.publishedAt || "").slice(0, 10),
      thumb: thumb,
      desc: (sn.description || "").split("\\n")[0].slice(0, 220),
      cat: cat
    };
  }

  // Tier 1: the 4 curated playlists (ground truth).
  function loadCuratedPlaylists(seen) {
    var promises = [];
    Object.keys(PLAYLISTS).forEach(function (cat) {
      PLAYLISTS[cat].forEach(function (pl) {
        promises.push(
          fetchPlaylist(pl.id).then(function (data) {
            (data.items || []).forEach(function (item) {
              var sn = item.snippet;
              var vid = sn.resourceId && sn.resourceId.videoId;
              if (!vid || seen[vid]) return;
              seen[vid] = true;
              // The "CSR Podcast" playlist includes some BRSR-focused
              // episodes — treat those as ESG & BRSR, not CSR.
              var effectiveCat = cat;
              if (cat === "csr" && /brsr/i.test(sn.title || "")) {
                effectiveCat = "esg";
              }
              allVideos.push(buildVideo(sn, vid, effectiveCat));
            });
          }).catch(function (err) {
            console.error("Failed to load playlist", pl.id, err);
          })
        );
      });
    });
    return Promise.all(promises);
  }

  // Tier 2: rest of the channel, classified by title keyword, for
  // anything relevant that hasn't been added to a curated playlist.
  function loadChannelFallback(seen) {
    var uploadsUrl = "https://www.googleapis.com/youtube/v3/channels"
      + "?part=contentDetails&id=" + CHANNEL_ID + "&key=" + YOUTUBE_API_KEY;

    return fetchJson(uploadsUrl).then(function (data) {
      var items = data.items || [];
      if (!items.length) throw new Error("Channel not found");
      var uploadsPlaylistId = items[0].contentDetails.relatedPlaylists.uploads;

      var collected = 0;

      function loadPage(pageToken) {
        var url = "https://www.googleapis.com/youtube/v3/playlistItems"
          + "?part=snippet&maxResults=50&playlistId=" + uploadsPlaylistId
          + "&key=" + YOUTUBE_API_KEY
          + (pageToken ? "&pageToken=" + pageToken : "");

        return fetchJson(url).then(function (pageData) {
          (pageData.items || []).forEach(function (item) {
            var sn = item.snippet;
            var vid = sn.resourceId && sn.resourceId.videoId;
            if (!vid || seen[vid]) return;
            var cat = classifyByKeyword(sn.title);
            if (!cat) return;
            seen[vid] = true;
            collected++;
            allVideos.push(buildVideo(sn, vid, cat));
          });

          if (pageData.nextPageToken && collected < MAX_FALLBACK_VIDEOS) {
            return loadPage(pageData.nextPageToken);
          }
        });
      }

      return loadPage(null);
    }).catch(function (err) {
      console.error("Channel-wide fallback scan failed", err);
    });
  }

  function loadAll() {
    var seen = {};
    return loadCuratedPlaylists(seen).then(function () {
      return loadChannelFallback(seen);
    });
  }

  function escapeHtml(s) {
    var div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function render() {
    var grid = document.getElementById("webinar-grid");
    var status = document.getElementById("webinar-status");
    var q = currentQuery.toLowerCase();

    var results = allVideos.filter(function (v) {
      if (currentCat && v.cat !== currentCat) return false;
      if (q && v.title.toLowerCase().indexOf(q) === -1) return false;
      return true;
    });
    results.sort(function (a, b) { return a.date < b.date ? 1 : -1; });

    grid.innerHTML = "";

    if (!results.length) {
      status.style.display = "block";
      status.textContent = "No webinars found"
        + (currentCat ? " in this category" : "")
        + (currentQuery ? " for \\u201c" + currentQuery + "\\u201d" : "") + ".";
      return;
    }
    status.style.display = "none";

    results.forEach(function (v) {
      var url = "https://www.youtube.com/watch?v=" + v.id;
      var card = document.createElement("div");
      card.className = "card webinar-card-v2";
      card.innerHTML =
        '<a class="webinar-thumb" href="' + url + '" target="_blank" rel="noopener">'
          + '<img src="' + v.thumb + '" alt="' + escapeHtml(v.title) + '">'
          + '<span class="webinar-play">\\u25B6</span>'
        + '</a>'
        + '<div class="webinar-card-body">'
          + '<p class="webinar-date-v2">' + v.date + '</p>'
          + '<h3><a href="' + url + '" target="_blank" rel="noopener">' + escapeHtml(v.title) + '</a></h3>'
          + '<p>' + escapeHtml(v.desc) + '</p>'
        + '</div>';
      grid.appendChild(card);
    });
  }

  document.getElementById("webinar-tabs").addEventListener("click", function (e) {
    var link = e.target.closest(".tab-link");
    if (!link) return;
    e.preventDefault();
    document.querySelectorAll("#webinar-tabs .tab-link").forEach(function (a) {
      a.classList.remove("active");
    });
    link.classList.add("active");
    currentCat = link.getAttribute("data-cat") || "";
    render();
  });

  document.getElementById("webinar-search-form").addEventListener("submit", function (e) {
    e.preventDefault();
  });
  document.getElementById("webinar-search-input").addEventListener("input", function (e) {
    currentQuery = e.target.value;
    render();
  });

  loadAll().then(render).catch(function (err) {
    document.getElementById("webinar-status").textContent =
      "Could not load videos from YouTube right now.";
    console.error(err);
  });
})();
</script>

{% endblock %}
"""

webinar_template_filled = WEBINAR_TEMPLATE.replace("%%YOUTUBE_API_KEY%%", YOUTUBE_API_KEY)

with app.test_request_context("/webinar/"):
    webinar_html = render_template_string(webinar_template_filled)
write_page("webinar/index.html", webinar_html)

print()
print("Build complete ->", OUTPUT)
