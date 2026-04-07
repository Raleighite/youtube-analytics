/* ── YouTube Analytics Tracker – Frontend ──────────────────────────────── */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ── Helpers ────────────────────────────────────────────────────────────

function fmt(n) {
    if (n == null) return "N/A";
    return Number(n).toLocaleString();
}

function headers() {
    const key = $("#apiKey").value.trim();
    const h = { "Content-Type": "application/json" };
    if (key) h["X-API-Key"] = key;
    return h;
}

function method() {
    return $("#fetchMethod").value;
}

function showError(el, msg) {
    el.textContent = msg;
    el.classList.remove("hidden");
}

function hideError(el) {
    el.classList.add("hidden");
}

function sourceBadge(src) {
    const cls = src === "api" ? "source-api" : "source-scrape";
    return `<span class="source-badge ${cls}">${src}</span>`;
}

// ── Tabs ──────────────────────────────────────────────────────────────

$$(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
        $$(".tab").forEach((t) => t.classList.remove("active"));
        $$(".tab-content").forEach((t) => t.classList.remove("active"));
        btn.classList.add("active");
        $(`#${btn.dataset.tab}`).classList.add("active");
    });
});

// ── Video Lookup ──────────────────────────────────────────────────────

$("#lookupVideos").addEventListener("click", async () => {
    const raw = $("#videoIds").value.trim();
    if (!raw) return;

    const ids = raw
        .split(/[\n,]+/)
        .map((s) => s.trim())
        .filter(Boolean);

    const loading = $("#videoLoading");
    const errorEl = $("#videoError");
    const resultsEl = $("#videoResults");

    loading.classList.remove("hidden");
    hideError(errorEl);
    resultsEl.innerHTML = "";

    try {
        const resp = await fetch("/api/videos", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({ video_ids: ids, method: method() }),
        });
        const data = await resp.json();

        if (!resp.ok) {
            showError(errorEl, data.error || "Request failed");
            return;
        }

        if (data.videos.length === 0) {
            showError(errorEl, "No videos found. Check your video IDs.");
            return;
        }

        resultsEl.innerHTML = data.videos
            .map(
                (v) => `
            <div class="video-card">
                ${v.thumbnail_url ? `<img src="${v.thumbnail_url}" alt="thumbnail" loading="lazy">` : ""}
                <div class="card-body">
                    <div class="card-title">${escapeHtml(v.title || v.video_id)}</div>
                    <div class="card-channel">${escapeHtml(v.channel_title || "")} ${sourceBadge(data.source)}</div>
                    <div class="stats-row">
                        <div class="stat"><span class="stat-value">${fmt(v.view_count)}</span><span class="stat-label">views</span></div>
                        <div class="stat"><span class="stat-value">${fmt(v.like_count)}</span><span class="stat-label">likes</span></div>
                        <div class="stat"><span class="stat-value">${fmt(v.comment_count)}</span><span class="stat-label">comments</span></div>
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn-small" onclick="showVideoHistory('${v.video_id}', '${escapeHtml(v.title || v.video_id)}')">View History</button>
                    <a class="btn-small" href="https://www.youtube.com/watch?v=${v.video_id}" target="_blank" rel="noopener">Open on YouTube</a>
                </div>
            </div>`
            )
            .join("");

        if (data.errors && data.errors.length > 0) {
            showError(errorEl, `Could not fetch: ${data.errors.join(", ")}`);
        }
    } catch (e) {
        showError(errorEl, `Network error: ${e.message}`);
    } finally {
        loading.classList.add("hidden");
    }
});

// ── Video History Modal ───────────────────────────────────────────────

let videoChartInstance = null;

async function showVideoHistory(videoId, title) {
    const modal = $("#historyModal");
    $("#historyModalTitle").textContent = `History: ${title}`;
    modal.classList.remove("hidden");

    try {
        const resp = await fetch(`/api/videos/${videoId}/history`);
        const data = await resp.json();
        const rows = data.history || [];

        const tbody = $("#historyTable tbody");
        tbody.innerHTML = rows
            .map(
                (r) => `
            <tr>
                <td>${new Date(r.fetched_at).toLocaleString()}</td>
                <td>${fmt(r.view_count)}</td>
                <td>${fmt(r.like_count)}</td>
                <td>${fmt(r.comment_count)}</td>
                <td>${sourceBadge(r.source)}</td>
            </tr>`
            )
            .join("");

        // Draw chart
        if (videoChartInstance) videoChartInstance.destroy();
        if (rows.length > 1) {
            const ctx = $("#videoChart").getContext("2d");
            videoChartInstance = new Chart(ctx, {
                type: "line",
                data: {
                    labels: rows.map((r) => new Date(r.fetched_at).toLocaleDateString()),
                    datasets: [
                        {
                            label: "Views",
                            data: rows.map((r) => r.view_count),
                            borderColor: "#3498db",
                            backgroundColor: "rgba(52,152,219,0.1)",
                            fill: true,
                            tension: 0.3,
                        },
                        {
                            label: "Likes",
                            data: rows.map((r) => r.like_count),
                            borderColor: "#2ecc71",
                            backgroundColor: "rgba(46,204,113,0.1)",
                            fill: true,
                            tension: 0.3,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: "#f1f1f1" } } },
                    scales: {
                        x: { ticks: { color: "#aaa" }, grid: { color: "#333" } },
                        y: { ticks: { color: "#aaa" }, grid: { color: "#333" } },
                    },
                },
            });
        }
    } catch (e) {
        console.error("Failed to load history:", e);
    }
}

$(".modal-close").addEventListener("click", () => {
    $("#historyModal").classList.add("hidden");
});

$("#historyModal").addEventListener("click", (e) => {
    if (e.target === $("#historyModal")) {
        $("#historyModal").classList.add("hidden");
    }
});

// ── Channel Lookup ────────────────────────────────────────────────────

$("#lookupChannel").addEventListener("click", async () => {
    const channelId = $("#channelId").value.trim();
    if (!channelId) return;

    const loading = $("#channelLoading");
    const errorEl = $("#channelError");
    const searchEl = $("#channelSearchResults");

    loading.classList.remove("hidden");
    hideError(errorEl);
    searchEl.classList.add("hidden");

    try {
        const resp = await fetch("/api/channels/lookup", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({ channel_id: channelId, method: method() }),
        });
        const data = await resp.json();

        if (!resp.ok) {
            showError(errorEl, data.error || "Request failed");
            return;
        }

        renderChannelCard(data.channel, data.source);
        loadChannelHistory(data.channel.channel_id);
        loadTrackedChannels();
    } catch (e) {
        showError(errorEl, `Network error: ${e.message}`);
    } finally {
        loading.classList.add("hidden");
    }
});

// ── Channel Search ────────────────────────────────────────────────────

$("#searchChannel").addEventListener("click", async () => {
    const query = $("#channelId").value.trim();
    if (!query) return;

    const loading = $("#channelLoading");
    const errorEl = $("#channelError");
    const searchEl = $("#channelSearchResults");

    loading.classList.remove("hidden");
    hideError(errorEl);
    searchEl.classList.add("hidden");

    try {
        const resp = await fetch("/api/channels/search", {
            method: "POST",
            headers: headers(),
            body: JSON.stringify({ query }),
        });
        const data = await resp.json();

        if (!resp.ok) {
            showError(errorEl, data.error || "Search failed");
            return;
        }

        if (!data.results || data.results.length === 0) {
            showError(errorEl, "No channels found.");
            return;
        }

        searchEl.innerHTML = data.results
            .map(
                (ch) => `
            <div class="search-item" onclick="selectChannel('${ch.channel_id}')">
                ${ch.thumbnail_url ? `<img src="${ch.thumbnail_url}" alt="">` : ""}
                <div>
                    <div style="font-weight:600">${escapeHtml(ch.channel_title)}</div>
                    <div style="font-size:0.8rem;color:var(--text-dim)">${ch.channel_id}</div>
                </div>
            </div>`
            )
            .join("");
        searchEl.classList.remove("hidden");
    } catch (e) {
        showError(errorEl, `Network error: ${e.message}`);
    } finally {
        loading.classList.add("hidden");
    }
});

function selectChannel(channelId) {
    $("#channelId").value = channelId;
    $("#channelSearchResults").classList.add("hidden");
    $("#lookupChannel").click();
}

// ── Render Channel ────────────────────────────────────────────────────

function renderChannelCard(ch, source) {
    const el = $("#channelResult");
    el.innerHTML = `
        ${ch.thumbnail_url ? `<img src="${ch.thumbnail_url}" alt="">` : ""}
        <div class="channel-info">
            <div class="channel-name">${escapeHtml(ch.channel_title || ch.channel_id)} ${sourceBadge(source)}</div>
            <div class="channel-id">${ch.channel_id}</div>
            <div class="channel-stats">
                <div><div class="channel-stat-value">${fmt(ch.subscriber_count)}</div><div class="channel-stat-label">subscribers</div></div>
                <div><div class="channel-stat-value">${fmt(ch.video_count)}</div><div class="channel-stat-label">videos</div></div>
                <div><div class="channel-stat-value">${fmt(ch.view_count)}</div><div class="channel-stat-label">total views</div></div>
            </div>
        </div>`;
    el.classList.remove("hidden");
}

// ── Channel History Chart ─────────────────────────────────────────────

let channelChartInstance = null;

async function loadChannelHistory(channelId) {
    const section = $("#channelHistorySection");

    try {
        const resp = await fetch(`/api/channels/${channelId}/history`);
        const data = await resp.json();
        const rows = data.history || [];

        if (rows.length < 2) {
            section.classList.add("hidden");
            return;
        }

        section.classList.remove("hidden");
        if (channelChartInstance) channelChartInstance.destroy();

        const ctx = $("#channelChart").getContext("2d");
        channelChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: rows.map((r) => new Date(r.fetched_at).toLocaleDateString()),
                datasets: [
                    {
                        label: "Subscribers",
                        data: rows.map((r) => r.subscriber_count),
                        borderColor: "#ff0000",
                        backgroundColor: "rgba(255,0,0,0.1)",
                        fill: true,
                        tension: 0.3,
                        yAxisID: "y",
                    },
                    {
                        label: "Videos",
                        data: rows.map((r) => r.video_count),
                        borderColor: "#3498db",
                        backgroundColor: "rgba(52,152,219,0.1)",
                        fill: true,
                        tension: 0.3,
                        yAxisID: "y1",
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "#f1f1f1" } } },
                scales: {
                    x: { ticks: { color: "#aaa" }, grid: { color: "#333" } },
                    y: {
                        type: "linear",
                        position: "left",
                        ticks: { color: "#ff0000" },
                        grid: { color: "#333" },
                        title: { display: true, text: "Subscribers", color: "#ff0000" },
                    },
                    y1: {
                        type: "linear",
                        position: "right",
                        ticks: { color: "#3498db" },
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: "Videos", color: "#3498db" },
                    },
                },
            },
        });
    } catch (e) {
        console.error("Failed to load channel history:", e);
    }
}

// ── Tracked Channels ──────────────────────────────────────────────────

async function loadTrackedChannels() {
    try {
        const resp = await fetch("/api/channels/tracked");
        const data = await resp.json();
        const channels = data.channels || [];

        const el = $("#trackedChannels");
        if (channels.length === 0) {
            el.innerHTML = '<p style="color:var(--text-dim);font-size:0.9rem">No channels tracked yet. Look up a channel to start tracking.</p>';
            return;
        }

        el.innerHTML = channels
            .map(
                (ch) => `
            <div class="tracked-item">
                <div class="tracked-item-info" onclick="selectChannel('${ch.channel_id}')">
                    <span style="font-weight:600">${escapeHtml(ch.channel_title || ch.channel_id)}</span>
                    <span style="font-size:0.8rem;color:var(--text-dim)">${ch.channel_id}</span>
                </div>
                <button class="btn-remove" onclick="removeTracked('${ch.channel_id}')">Remove</button>
            </div>`
            )
            .join("");
    } catch (e) {
        console.error("Failed to load tracked channels:", e);
    }
}

async function removeTracked(channelId) {
    try {
        await fetch(`/api/channels/${channelId}/track`, { method: "DELETE" });
        loadTrackedChannels();
    } catch (e) {
        console.error("Failed to remove channel:", e);
    }
}

// ── Utils ─────────────────────────────────────────────────────────────

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ── Persist API key in sessionStorage ─────────────────────────────────

const savedKey = sessionStorage.getItem("yt_api_key");
if (savedKey) $("#apiKey").value = savedKey;
$("#apiKey").addEventListener("input", () => {
    sessionStorage.setItem("yt_api_key", $("#apiKey").value);
});

// ── Init ──────────────────────────────────────────────────────────────

loadTrackedChannels();
