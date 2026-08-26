const CHANNELS = ["D1", "D2", "D3"];

const app = document.querySelector("#app");
let benchmarkIndex = null;
let overviewFilters = {
  query: "",
  platform: "all",
  evidence: new Set(),
};
let taskFilters = {};
let expandedTasks = new Set();

async function init() {
  try {
    const response = await fetch("data/benchmark_index.json");
    if (!response.ok) {
      throw new Error(`benchmark_index.json returned ${response.status}`);
    }
    benchmarkIndex = await response.json();
    window.addEventListener("hashchange", renderRoute);
    renderRoute();
  } catch (error) {
    app.innerHTML = `
      <header class="hero">
        <p class="eyebrow">Benchmark Construction Browser</p>
        <h1>Drift Benchmark Explorer</h1>
        <p class="hero-copy">Could not load <code>data/benchmark_index.json</code>. Run <code>python drift_web/build_site.py --root data/C_drift_benchmark --root data/D_drift_benchmark</code> and refresh.</p>
        <pre>${escapeHtml(error.message)}</pre>
      </header>
    `;
  }
}

function renderRoute() {
  if (!benchmarkIndex) return;
  const match = window.location.hash.match(/^#\/family\/(.+)$/);
  if (match) {
    const familyId = decodeURIComponent(match[1]);
    const family = benchmarkIndex.families.find((item) => item.id === familyId);
    if (family) {
      renderFamily(family);
      return;
    }
  }
  renderOverview();
}

function renderOverview() {
  const families = filteredFamilies();
  const platforms = [...new Set(benchmarkIndex.families.map((family) => family.platform))].sort();
  const totalTasks = benchmarkIndex.families.reduce((sum, family) => sum + family.task_count, 0);
  const bfclCount = benchmarkIndex.families.filter((family) => family.platform === "BFCL").length;
  const designCount = benchmarkIndex.families.length - bfclCount;

  app.innerHTML = `
    <header class="hero">
      <p class="eyebrow">Benchmark Construction Browser</p>
      <h1>Drift Benchmark Explorer</h1>
      <p class="hero-copy">Browse drift benchmark families, inspect sibling tasks, compare evidence regimes, and read the construction plans generated from files on disk.</p>
      <div class="summary-grid" aria-label="Benchmark summary">
        ${summaryItem("Families", benchmarkIndex.families.length)}
        ${summaryItem("Tasks", totalTasks)}
        ${summaryItem("BFCL Families", bfclCount)}
        ${summaryItem("Design-Level Families", designCount)}
        ${summaryItem("Generated", formatTimestamp(benchmarkIndex.generated_at))}
      </div>
    </header>
    <section class="toolbar" aria-label="Overview filters">
      <label class="field grow">
        <span class="filter-label">Search families</span>
        <input id="family-search" type="search" value="${escapeAttribute(overviewFilters.query)}" placeholder="Family ID, title, mechanism, or drift summary" />
      </label>
      <label class="field">
        <span class="filter-label">Platform</span>
        <select id="platform-filter">
          <option value="all">All platforms</option>
          ${platforms.map((platform) => `<option value="${escapeAttribute(platform)}" ${overviewFilters.platform === platform ? "selected" : ""}>${escapeHtml(platform)}</option>`).join("")}
        </select>
      </label>
      <div class="field">
        <span class="filter-label">Require evidence channel</span>
        <div class="evidence-filters">
          ${CHANNELS.map((channel) => `
            <label class="toggle">
              <input type="checkbox" value="${channel}" ${overviewFilters.evidence.has(channel) ? "checked" : ""} />
              ${channel}
            </label>
          `).join("")}
        </div>
      </div>
    </section>
    <main>
      ${families.length ? `<section class="family-grid">${families.map(renderFamilyCard).join("")}</section>` : `<p class="empty-state">No families match the current filters.</p>`}
    </main>
  `;

  document.querySelector("#family-search").addEventListener("input", (event) => {
    overviewFilters.query = event.target.value;
    renderOverview();
  });
  document.querySelector("#platform-filter").addEventListener("change", (event) => {
    overviewFilters.platform = event.target.value;
    renderOverview();
  });
  document.querySelectorAll(".evidence-filters input").forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      if (event.target.checked) {
        overviewFilters.evidence.add(event.target.value);
      } else {
        overviewFilters.evidence.delete(event.target.value);
      }
      renderOverview();
    });
  });
}

function filteredFamilies() {
  const query = overviewFilters.query.trim().toLowerCase();
  return benchmarkIndex.families.filter((family) => {
    const searchable = [family.id, family.title, family.platform, family.mechanism, family.drift_summary].join(" ").toLowerCase();
    if (query && !searchable.includes(query)) return false;
    if (overviewFilters.platform !== "all" && family.platform !== overviewFilters.platform) return false;
    for (const channel of overviewFilters.evidence) {
      if (!family.evidence[channel].present) return false;
    }
    return true;
  });
}

function renderFamilyCard(family) {
  return `
    <article class="family-card">
      <div>
        <span class="family-id">${escapeHtml(family.id)}</span>
        <h2 class="card-title">${escapeHtml(family.title)}</h2>
        <p class="meta">${escapeHtml(family.mechanism || family.platform)}</p>
        <div class="badge-row">
          <span class="badge">${escapeHtml(family.platform)}</span>
          ${family.platform.includes("design") ? `<span class="badge design">Design-level</span>` : ""}
          <span class="badge">${escapeHtml(family.status_label)}</span>
        </div>
        <p class="card-summary">${escapeHtml(family.drift_summary)}</p>
        <strong class="summary-value">${family.task_count}</strong>
        <span class="summary-label">tasks</span>
        ${renderEvidenceLines(family.evidence)}
      </div>
      <div class="card-footer">
        <a class="button-link" href="#/family/${encodeURIComponent(family.id)}">Inspect family</a>
        ${family.paired_family ? `<span class="meta">Paired with <span class="family-id">${escapeHtml(family.paired_family)}</span></span>` : ""}
      </div>
    </article>
  `;
}

function renderFamily(family) {
  const filters = taskFilters[family.id] || { query: "", slice: "all" };
  const filteredTasks = filterTasks(family, filters);
  const slices = [...new Set(family.tasks.map((task) => task.slice))].sort();

  app.innerHTML = `
    <header class="hero">
      <p><a href="#">Back to overview</a></p>
      <div class="detail-header">
        <div>
          <p class="eyebrow">Family Detail</p>
          <h1><span class="family-id">${escapeHtml(family.id)}</span> ${escapeHtml(family.title)}</h1>
          <p class="hero-copy">${escapeHtml(family.drift_summary)}</p>
        </div>
        <div class="badge-row">
          <span class="badge">${escapeHtml(family.platform)}</span>
          ${family.platform.includes("design") ? `<span class="badge design">Design-level</span>` : ""}
          <span class="badge">${escapeHtml(family.status_label)}</span>
          <span class="badge">${family.task_count} tasks</span>
        </div>
      </div>
      ${family.paired_family ? `
        <div class="paired-note">
          Paired evidence condition: <a href="#/family/${encodeURIComponent(family.paired_family)}">View ${escapeHtml(family.paired_family)}</a>.
        </div>
      ` : ""}
      ${family.family_notes && family.family_notes.length ? `
        <div class="paired-note">
          ${family.family_notes.map((note) => `<p>${escapeHtml(note)}</p>`).join("")}
        </div>
      ` : ""}
    </header>

    <section class="panel" aria-labelledby="evidence-heading">
      <h2 id="evidence-heading">Evidence Composition</h2>
      <div class="evidence-stack">${renderStackedBar(family.evidence)}</div>
      <div class="evidence-cards">
        ${CHANNELS.map((channel) => renderEvidenceCard(channel, family)).join("")}
      </div>
    </section>

    <section class="task-panel" aria-labelledby="tasks-heading">
      <h2 id="tasks-heading">Sibling Tasks</h2>
      <div class="task-toolbar">
        <label class="field grow">
          <span class="filter-label">Search tasks</span>
          <input id="task-search" type="search" value="${escapeAttribute(filters.query)}" placeholder="Task ID, description, or instruction" />
        </label>
        <label class="field">
          <span class="filter-label">Slice</span>
          <select id="slice-filter">
            <option value="all">All slices</option>
            ${slices.map((slice) => `<option value="${escapeAttribute(slice)}" ${filters.slice === slice ? "selected" : ""}>${escapeHtml(slice)}</option>`).join("")}
          </select>
        </label>
      </div>
      ${filteredTasks.length ? renderTaskTable(filteredTasks) : `<p class="empty-state">No tasks match the current filters.</p>`}
    </section>

    <section class="plan-panel" aria-labelledby="plan-heading">
      <h2 id="plan-heading">Execution Plan</h2>
      ${family.plan ? `<p><a href="${escapeAttribute(family.plan.asset_path)}">Raw Markdown: ${escapeHtml(family.plan.filename)}</a></p><div id="plan-content" class="markdown-plan">Loading execution plan...</div>` : `<p class="empty-state">No execution plan was discovered.</p>`}
    </section>

    <section class="files-panel" aria-labelledby="files-heading">
      <h2 id="files-heading">Files</h2>
      ${renderFilesManifest(family.files_manifest)}
    </section>
  `;

  document.querySelector("#task-search").addEventListener("input", (event) => {
    taskFilters[family.id] = { ...filters, query: event.target.value };
    renderFamily(family);
  });
  document.querySelector("#slice-filter").addEventListener("change", (event) => {
    taskFilters[family.id] = { ...filters, slice: event.target.value };
    renderFamily(family);
  });
  document.querySelectorAll("[data-task-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const taskId = button.getAttribute("data-task-id");
      const key = `${family.id}:${taskId}`;
      if (expandedTasks.has(key)) {
        expandedTasks.delete(key);
      } else {
        expandedTasks.add(key);
      }
      renderFamily(family);
    });
  });
  if (family.plan) {
    loadPlan(family);
  }
}

function filterTasks(family, filters) {
  const query = filters.query.trim().toLowerCase();
  return family.tasks.filter((task) => {
    if (filters.slice !== "all" && task.slice !== filters.slice) return false;
    const searchable = [task.id, task.slice, task.description, task.instruction || ""].join(" ").toLowerCase();
    return !query || searchable.includes(query);
  });
}

function renderTaskTable(tasks) {
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Task ID</th>
            <th>Slice</th>
            <th>What is being drifted / stressed</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          ${tasks.map(renderTaskRows).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderTaskRows(task) {
  const familyId = currentFamilyId();
  const key = `${familyId}:${task.id}`;
  const expanded = expandedTasks.has(key);
  return `
    <tr class="task-row">
      <td><span class="task-id">${escapeHtml(task.id)}</span></td>
      <td><span class="badge ${task.slice.includes("affected") ? "affected" : ""}">${escapeHtml(task.slice)}</span></td>
      <td>${escapeHtml(task.description)}</td>
      <td><button class="button" type="button" data-task-id="${escapeAttribute(task.id)}">${expanded ? "Hide" : "Show"}</button></td>
    </tr>
    ${expanded ? `
      <tr class="task-detail-row">
        <td colspan="4">${renderTaskDetails(task)}</td>
      </tr>
    ` : ""}
  `;
}

function currentFamilyId() {
  const match = window.location.hash.match(/^#\/family\/(.+)$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function renderTaskDetails(task) {
  const entries = Object.entries(task.details || {});
  const blocks = [];
  if (task.instruction) {
    blocks.push(detailBlock("Full Instruction", task.instruction));
  }
  for (const [key, value] of entries) {
    if (key === "instruction" || key === "question") continue;
    blocks.push(detailBlock(labelize(key), value));
  }
  blocks.push(detailBlock("Source File", task.source_file));
  return `<div class="task-details">${blocks.join("")}</div>`;
}

function detailBlock(label, value) {
  const rendered = typeof value === "string" ? `<p>${escapeHtml(value)}</p>` : `<pre>${escapeHtml(JSON.stringify(value, null, 2))}</pre>`;
  return `<div class="detail-block"><h4>${escapeHtml(label)}</h4>${rendered}</div>`;
}

function renderEvidenceLines(evidence) {
  return `
    <div class="evidence-list">
      ${CHANNELS.map((channel) => `
        <div class="evidence-line">
          <span>${channel} ${evidence[channel].percentage}%</span>
          <div class="bar-track" aria-label="${channel} ${evidence[channel].percentage}%">
            <span class="segment ${channel.toLowerCase()}" style="width: ${evidence[channel].percentage}%"></span>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderStackedBar(evidence) {
  return `
    <div class="bar-track" aria-label="Evidence composition">
      ${CHANNELS.map((channel) => `<span class="segment ${channel.toLowerCase()}" style="width: ${evidence[channel].percentage}%"></span>`).join("")}
    </div>
    <div class="badge-row">
      ${CHANNELS.map((channel) => `<span class="badge">${channel} ${evidence[channel].percentage}%</span>`).join("")}
    </div>
  `;
}

function renderEvidenceCard(channel, family) {
  const item = family.evidence[channel];
  return `
    <article class="evidence-card ${channel.toLowerCase()}">
      <h3>${channel}</h3>
      <div class="evidence-percent">${item.percentage}%</div>
      ${item.present ? `
        <p><strong>How the agent receives it:</strong></p>
        <p>${escapeHtml(item.delivery || "No delivery description provided.")}</p>
      ` : `<p>Not provided in this family.</p>`}
      <p class="meta">Evidence files:</p>
      ${item.files.length ? `
        <ul class="file-list">
          ${item.files.map((file) => `<li><a href="${evidenceAssetPath(family.id, file)}">${escapeHtml(file)}</a></li>`).join("")}
        </ul>
      ` : `<p class="muted">No files discovered for this channel.</p>`}
    </article>
  `;
}

function renderFilesManifest(files) {
  if (!files || !files.length) {
    return `<p class="empty-state">No inspection files were discovered.</p>`;
  }
  return `
    <ul class="files-grid">
      ${files.map((file) => `<li><span class="mono">${escapeHtml(file.path)}</span><br /><span class="meta">${escapeHtml(file.kind)}</span></li>`).join("")}
    </ul>
  `;
}

async function loadPlan(family) {
  const target = document.querySelector("#plan-content");
  if (!target || !family.plan) return;
  try {
    const response = await fetch(family.plan.html_asset_path || family.plan.asset_path);
    if (!response.ok) throw new Error(`Execution plan returned ${response.status}`);
    if (family.plan.html_asset_path) {
      target.innerHTML = await response.text();
    } else {
      target.innerHTML = `<pre>${escapeHtml(await response.text())}</pre>`;
    }
  } catch (error) {
    target.innerHTML = `<p class="empty-state">Could not load execution plan: ${escapeHtml(error.message)}</p>`;
  }
}

function evidenceAssetPath(familyId, file) {
  return `assets/evidence/${encodeURIComponent(familyId)}/${file.split("/").map(encodeURIComponent).join("/")}`;
}

function summaryItem(label, value) {
  return `
    <div class="summary-item">
      <span class="summary-value">${escapeHtml(String(value))}</span>
      <span class="summary-label">${escapeHtml(label)}</span>
    </div>
  `;
}

function formatTimestamp(value) {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function labelize(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

init();
