'use strict';
const $ = id => document.getElementById(id);
const number = value => value == null ? '—' : new Intl.NumberFormat('en-US').format(value);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const time = value => value ? new Date(value * 1000).toLocaleTimeString('en-GB', {timeZone:'Asia/Bangkok',hour12:false}) : '—';
const age = value => value == null ? '—' : value < 60 ? `${Math.floor(value)}s ago` : value < 3600 ? `${Math.floor(value/60)}m ago` : `${(value/3600).toFixed(1)}h ago`;
const isActive = job => ['running','starting','stale'].includes(job.state);
const isFailed = job => ['failed','interrupted'].includes(job.state);
const descriptions = {A:'Stored weights · vector Huber',B:'Uniform relabel · vector Huber',C:'Stored weights · utility auxiliary',D:'Uniform relabel · utility auxiliary'};
let data = null, selected = null, stream = 'stderr', paused = false, busy = false, detailVersion = 0;

function badge(state) { return `<span class="badge ${esc(state.replaceAll(' ','-'))}">${esc(state.toUpperCase())}</span>`; }
function renderJobs() {
  if (!data) return;
  const filter = $('filter').value;
  const rows = data.jobs.filter(j => filter === 'all' || (filter === 'active' && isActive(j)) || (filter === 'failed' && isFailed(j)) || j.state === filter);
  $('jobs').innerHTML = rows.length ? rows.map(j => {
    const percentage = Math.min(100, Math.max(0, (j.step || 0) / j.budget * 100));
    return `<tr class="${j.name === selected ? 'selected' : ''}"><td><button type="button" class="worker-button" data-job="${esc(j.name)}" aria-pressed="${j.name === selected}"><strong>ARM ${esc(j.arm)}</strong><span class="seed">${esc(j.seed)}</span></button></td><td>${badge(j.state)}</td><td>${number(j.step)} <span class="unit">/ 500k</span><div class="row-progress ${isFailed(j) ? 'error' : ''}"><span style="width:${percentage}%"></span></div></td><td>${number(j.updates)}</td><td class="${isActive(j) && j.heartbeat_age > 300 ? 'age-warning' : ''}">${j.state === 'complete' ? 'Finalized' : age(j.heartbeat_age)}</td></tr>`;
  }).join('') : '<tr><td colspan="5" class="empty">No workers match this filter.</td></tr>';
  $('worker-count').textContent = `${rows.length} of ${data.jobs.length} workers`;
  $('jobs').querySelectorAll('button[data-job]').forEach(button => button.addEventListener('click', () => {
    selected = button.dataset.job; renderJobs(); renderInspector(); loadDetail();
  }));
}

function renderInspector() {
  const j = data?.jobs.find(job => job.name === selected);
  if (!j) return;
  $('selected-name').textContent = `ARM ${j.arm} / SEED ${j.seed}`;
  $('arm-description').textContent = descriptions[j.arm] || '';
  $('selected-badge').outerHTML = badge(j.state).replace('<span ', '<span id="selected-badge" ');
  $('selected-pid').textContent = j.pid ? `${j.pid} · ${j.alive === true ? 'alive' : j.alive === false ? 'exited' : 'unverified'}` : j.state === 'complete' ? 'Exited · finalized' : j.state === 'pending' ? 'Not started' : 'Not running';
  $('selected-resume').textContent = j.resume_available ? `${number(j.resume_step)} steps` : 'Not saved yet';
  $('selected-rate').textContent = j.rate ? `${Math.round(j.rate)} steps/s` : 'Not recorded';
  $('selected-task').textContent = j.task.length ? j.task.map(r => `${r.successes}/${r.episodes}`).join(' · ') : 'Not evaluated';
  $('selected-task').title = 'Final deliveries at task profile 0 and profile 1, respectively. Separate from training completion.';
}

function render(snapshot) {
  data = snapshot;
  if (!data.jobs.some(j => j.name === selected)) selected = data.jobs.find(isFailed)?.name || data.jobs.find(isActive)?.name || data.jobs[0]?.name;
  const percent = Math.min(100, 100 * data.total_steps / data.budget);
  $('percentage').textContent = percent.toFixed(1);
  $('steps').textContent = number(data.total_steps); $('budget').textContent = number(data.budget);
  $('source').textContent = data.source_commit?.slice(0,7) || 'Unavailable';
  $('study').textContent = data.study_id; $('session').textContent = 'LOCAL-01';
  $('run-status').outerHTML = badge(data.state).replace('<span ', '<span id="run-status" ');
  $('progress-track').innerHTML = data.jobs.map(j => `<div class="segment ${esc(j.state)}" title="${esc(j.name)}: ${number(j.step)} steps"><span style="width:${Math.min(100, 100*(j.step||0)/j.budget)}%"></span></div>`).join('');
  $('progress-track').setAttribute('aria-valuenow', percent.toFixed(1));
  $('done').textContent = data.counts.complete;
  $('active').textContent = data.jobs.filter(isActive).length;
  $('failed').textContent = data.jobs.filter(isFailed).length;
  $('pending').textContent = data.jobs.filter(j => j.state.includes('pending')).length;
  $('sampled').textContent = `${time(data.observed_unix)} ICT`;
  const gpu = data.gpu;
  $('gpu-name').textContent = gpu.available ? gpu.name.replace('NVIDIA GeForce ','') : 'GPU telemetry unavailable';
  $('gpu-available').textContent = gpu.available ? 'CUDA' : 'N/A';
  $('gpu-load').textContent = gpu.available ? gpu.utilization : '—';
  $('gpu-meter').style.width = `${gpu.available ? gpu.utilization : 0}%`;
  $('gpu-memory').textContent = gpu.available ? `${number(gpu.memory_used)} / ${number(gpu.memory_total)} MiB` : '—';
  $('gpu-temp').textContent = gpu.available ? `${gpu.temperature} °C` : '—';
  $('disk-work').textContent = data.disks_gib.workspace == null ? '—' : `${data.disks_gib.workspace} GiB`;
  $('disk-system').textContent = data.disks_gib.system == null ? '—' : `${data.disks_gib.system} GiB`;
  const failures = data.jobs.filter(isFailed);
  let title, text;
  if (failures.length) {
    title = data.coordinator_alive ? 'Dispatch halted · active workers finishing' : 'Recovery required · dispatch stopped';
    text = `${failures.map(j => `Arm ${j.arm}, seed ${j.seed}`).join('; ')} needs attention. ${data.jobs.filter(isActive).length} workers are active. Inspect stderr below; this console does not restart training.`;
  } else if (data.analysis) {
    title = 'Cohort finished · analysis available';
    text = `Audit: ${data.analysis.audit}. Qualified intervention arms: ${data.analysis.passing_arms.join(', ') || 'none'}. Training completion does not establish task competence.`;
  } else if (data.state === 'unavailable') {
    title = 'Experiment telemetry unavailable'; text = 'The local run directory is missing or its execution status could not be read. No training status is inferred.';
  } else if (!data.coordinator_alive) {
    title = 'Coordinator not confirmed alive'; text = 'Check the worker rows and retained logs. Stored running flags alone do not confirm an active process.';
  } else {
    title = 'Cohort running · fixed budget'; text = 'Each worker has a 500,000-step budget. Live process commands are checked on every sample. Progress logs update every 25k steps.';
  }
  $('alert').className = `status-banner${failures.length || !data.coordinator_alive ? '' : ' ok'}`;
  $('alert-title').textContent = title; $('alert-text').textContent = text + (data.warnings.length ? ` Read warnings: ${data.warnings.join('; ')}.` : '');
  $('footer-state').textContent = `${data.state} · ${data.counts.complete}/${data.jobs.length} jobs complete`;
  renderJobs(); renderInspector();
}

function plotLoss(losses) {
  const points = losses.filter(p => Number.isFinite(p.loss) && Number.isFinite(p.step));
  $('loss-value').textContent = points.length ? points.at(-1).loss.toPrecision(4) : '—';
  if (points.length < 2) {
    $('loss-plot').innerHTML = '<span class="muted">No recorded loss history yet.</span>';
    $('loss-note').textContent = 'This worker writes loss history at completion. No live curve is inferred.';
    return;
  }
  const values = points.map(p => p.loss), low = Math.min(...values), high = Math.max(...values);
  const first = points[0].step, last = points.at(-1).step;
  const path = points.map(p => `${8 + 264 * (p.step-first)/Math.max(1,last-first)},${82 - 70*(p.loss-low)/Math.max(1e-12,high-low)}`).join(' ');
  $('loss-plot').innerHTML = `<svg viewBox="0 0 280 95" preserveAspectRatio="none" role="img" aria-label="Recorded training loss over interactions"><line x1="8" y1="82" x2="272" y2="82"/><line x1="8" y1="12" x2="272" y2="12"/><polyline points="${path}"/></svg>`;
  $('loss-note').textContent = `${points.length} recorded samples · ${number(first)}–${number(last)} interactions. Loss alone does not establish task success.`;
}

async function request(url) {
  const response = await fetch(url, {cache:'no-store', signal:AbortSignal.timeout(8000)});
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
async function loadDetail() {
  if (!selected) return;
  const version = ++detailVersion;
  try {
    const detail = await request(`/api/job?name=${encodeURIComponent(selected)}&stream=${stream}`);
    if (version !== detailVersion) return;
    const log = $('log'), atBottom = log.scrollTop + log.clientHeight >= log.scrollHeight - 35;
    log.textContent = detail.log || 'Log is empty.';
    if (atBottom) log.scrollTop = log.scrollHeight;
    $('log-name').textContent = `${detail.name}.${detail.stream}.log`;
    $('log-modified').textContent = `Written ${time(detail.modified_unix)} ICT`;
    plotLoss(detail.losses);
  } catch (error) {
    if (version !== detailVersion) return;
    $('log').textContent = `Telemetry unavailable: ${error.message}. Last selection: ${selected}.`;
  }
}
async function refresh() {
  if (busy) return;
  busy = true;
  try {
    render(await request('/api/state'));
    $('offline').classList.add('hidden');
    $('connection').textContent = paused ? 'VIEW PAUSED' : 'CONNECTED';
    $('connection-dot').className = paused ? 'dot amber' : 'dot';
    await loadDetail();
  } catch (error) {
    $('connection').textContent = 'DISCONNECTED'; $('connection-dot').className = 'dot red';
    $('offline').textContent = `Monitor connection lost (${error.message}). Displayed values are the last received sample; this does not mean training stopped. Reopen START_TRAINING_MONITOR.bat if the server was closed.`;
    $('offline').classList.remove('hidden');
  } finally { busy = false; }
}
$('filter').addEventListener('change', renderJobs);
$('refresh').addEventListener('click', refresh);
$('pause').addEventListener('click', () => {
  paused = !paused; $('pause').textContent = paused ? 'Resume view' : 'Pause view';
  $('refresh-label').textContent = paused ? 'VIEW PAUSED · TRAINING UNAFFECTED' : 'AUTO REFRESH 5s';
  $('connection').textContent = paused ? 'VIEW PAUSED' : 'CONNECTED';
  $('connection-dot').className = paused ? 'dot amber' : 'dot';
  if (!paused) refresh();
});
for (const tab of ['stderr','stdout']) $('tab-'+tab).addEventListener('click', () => {
  stream = tab;
  for (const name of ['stderr','stdout']) $('tab-'+name).setAttribute('aria-selected', String(name === tab));
  loadDetail();
});
document.addEventListener('keydown', event => {
  if (event.key.toLowerCase() === 'r' && !['INPUT','SELECT','TEXTAREA'].includes(event.target.tagName) && !event.ctrlKey && !event.metaKey) refresh();
});
setInterval(() => { $('clock').textContent = `${time(Date.now()/1000)} ICT`; }, 1000);
setInterval(() => { if (!paused && !document.hidden) refresh(); }, 5000);
document.addEventListener('visibilitychange', () => { if (!document.hidden && !paused) refresh(); });
refresh();
