const BOARD_PATH = '../board';

const state = {
  dashboard: null,
  activeView: 'overview',
};

const elements = {
  refreshButton: document.getElementById('refresh-button'),
  pageTitle: document.getElementById('page-title'),
  summaryGrid: document.getElementById('summary-grid'),
  requestsTable: document.getElementById('requests-table'),
  workItemsTable: document.getElementById('work-items-table'),
  tasksTable: document.getElementById('tasks-table'),
  blockedTable: document.getElementById('blocked-table'),
  escalationsTable: document.getElementById('escalations-table'),
  statusChart: document.getElementById('status-chart'),
  throughputChart: document.getElementById('throughput-chart'),
};

const navButtons = [...document.querySelectorAll('.nav-item')];

navButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const nextView = button.dataset.view;
    state.activeView = nextView;
    updateView();
  });
});

elements.refreshButton.addEventListener('click', () => {
  loadDashboard();
});

function updateView() {
  const viewNames = ['overview', 'requests', 'work-items', 'tasks', 'blocked'];

  viewNames.forEach((name) => {
    const viewElement = document.getElementById(`${name}-view`);
    if (viewElement) {
      viewElement.classList.toggle('active', name === state.activeView);
    }
  });

  navButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.view === state.activeView);
  });

  const labels = {
    overview: 'Overview',
    requests: 'Requests',
    workItems: 'Work items',
    'work-items': 'Work items',
    tasks: 'Tasks',
    blocked: 'Blocked',
  };

  elements.pageTitle.textContent = labels[state.activeView] || 'Overview';
}

async function loadDashboard() {
  try {
    const files = await collectBoardFiles();
    const workItems = await Promise.all(files.map(readJsonFile));
    const dashboard = buildDashboard(workItems.filter(Boolean));
    state.dashboard = dashboard;
    renderSummary(dashboard.summary);
    renderStatusChart(dashboard.statusBreakdown);
    renderThroughputChart(dashboard.throughputTrend);
    renderRequestsTable(dashboard.requests);
    renderWorkItemsTable(dashboard.workItems);
    renderTaskTable(dashboard.tasks);
    renderBlockedTable(dashboard.blocked);
    renderEscalationsTable(dashboard.escalations);
  } catch (error) {
    console.error(error);
    showErrorState(error.message || 'Unable to load data');
  }
}

async function collectBoardFiles() {
  const boardRoot = await fetch(`${BOARD_PATH}/index.json`).catch(() => null);

  if (boardRoot && boardRoot.ok) {
    return getFilesFromManifest(await boardRoot.json());
  }

  const response = await fetch(`${BOARD_PATH}/`);
  if (!response.ok) {
    return [];
  }

  const html = await response.text();
  const linkPaths = [...new Set((html.match(/href="([^"]+)"/g) || []).map((value) => value.replace('href="', '').replace('"', '')))].filter((value) => value.endsWith('/'));
  const requestFolders = linkPaths.filter((value) => !value.startsWith('.') && !value.startsWith('/') && value !== '');

  const files = [];
  for (const folder of requestFolders) {
    const requestUrl = `${BOARD_PATH}/${folder}`;
    const requestResponse = await fetch(requestUrl);
    if (!requestResponse.ok) {
      continue;
    }

    const requestHtml = await requestResponse.text();
    const fileMatches = [...requestHtml.matchAll(/href="([^"]+\.work-item\.json)"/g)];
    fileMatches.forEach((match) => files.push(`${BOARD_PATH}/${folder}${match[1]}`));
  }

  return files;
}

function getFilesFromManifest(manifest) {
  if (!manifest || !Array.isArray(manifest.files)) {
    return [];
  }

  return manifest.files.filter((filePath) => filePath.endsWith('.work-item.json')).map((filePath) => `${BOARD_PATH}/${filePath}`);
}

async function readJsonFile(filePath) {
  const response = await fetch(filePath);
  if (!response.ok) {
    return null;
  }
  return response.json();
}

function showErrorState(message) {
  const emptyT = '<div class="empty-state">Unable to load ADLC board data. ' + escapeHtml(message) + '</div>';
  elements.summaryGrid.innerHTML = emptyT;
  elements.requestsTable.innerHTML = emptyT;
  elements.workItemsTable.innerHTML = emptyT;
  elements.tasksTable.innerHTML = emptyT;
  elements.blockedTable.innerHTML = emptyT;
  elements.escalationsTable.innerHTML = emptyT;
  elements.statusChart.innerHTML = '';
  elements.throughputChart.innerHTML = '';
}

function buildDashboard(workItems) {
  const requests = {};
  const tasks = [];
  const escalations = [];

  for (const workItem of workItems) {
    const requestId = workItem.requestId || (workItem.id ? workItem.id.split('-').slice(0, 2).join('-') : 'unknown');
    if (!requests[requestId]) {
      requests[requestId] = {
        id: requestId,
        count: 0,
        items: [],
      };
    }

    requests[requestId].count += 1;
    requests[requestId].items.push(workItem);

    for (const task of workItem.tasks || []) {
      tasks.push({
        ...task,
        workItemId: workItem.id,
        requestId,
      });
    }

    for (const escalation of workItem.execution?.escalations || []) {
      escalations.push({
        ...escalation,
        workItemId: workItem.id,
        requestId,
      });
    }
  }

  const statusBreakdown = {
    new: 0,
    'in-progress': 0,
    done: 0,
    blocked: 0,
  };

  for (const item of workItems) {
    const status = item.status || 'new';
    if (statusBreakdown[status] !== undefined) {
      statusBreakdown[status] += 1;
    }
  }

  const throughputTrend = workItems
    .map((item) => ({
      label: item.id || 'unknown',
      value: item.execution?.totals?.totalTokens || 0,
    }))
    .slice(0, 8);

  const totalCost = workItems.reduce((sum, item) => sum + ((item.execution?.totals?.estimatedCostUsd) || 0), 0);

  const summary = {
    totalRequests: Object.keys(requests).length,
    totalWorkItems: workItems.length,
    blocked: statusBreakdown.blocked,
    done: statusBreakdown.done,
    avgLeadTime: workItems.length ? (workItems.reduce((sum, item) => sum + (item.execution?.totals?.durationSeconds || 0), 0) / workItems.length).toFixed(1) : '0.0',
    totalCost: totalCost.toFixed(2),
  };

  return {
    summary,
    statusBreakdown,
    throughputTrend,
    requests: Object.values(requests),
    workItems,
    tasks,
    blocked: workItems.filter((item) => (item.status || 'new') === 'blocked'),
    escalations: escalations.slice(0, 10),
  };
}

function renderSummary(summary) {
  const cards = [
    { label: 'Requests', value: summary.totalRequests },
    { label: 'Work items', value: summary.totalWorkItems },
    { label: 'Blocked', value: summary.blocked },
    { label: 'Done', value: summary.done },
    { label: 'Avg. lead time (s)', value: summary.avgLeadTime },
    { label: 'Total cost ($)', value: summary.totalCost },
  ];

  elements.summaryGrid.innerHTML = cards.map((card) => `
    <div class="summary-card">
      <div class="label">${escapeHtml(card.label)}</div>
      <div class="value">${escapeHtml(String(card.value))}</div>
    </div>
  `).join('');
}

function renderStatusChart(statusBreakdown) {
  const svg = elements.statusChart;
  svg.innerHTML = '';

  const data = [
    { label: 'New', value: statusBreakdown.new, color: '#86aefc' },
    { label: 'In progress', value: statusBreakdown['in-progress'], color: '#f7c97f' },
    { label: 'Done', value: statusBreakdown.done, color: '#5dd39e' },
    { label: 'Blocked', value: statusBreakdown.blocked, color: '#f57b7b' },
  ];

  const maxValue = Math.max(1, ...data.map((item) => item.value));
  const barWidth = 48;
  const gap = 28;
  const chartHeight = 160;

  data.forEach((item, index) => {
    const x = 40 + index * (barWidth + gap);
    const height = (item.value / maxValue) * chartHeight;
    const y = 180 - height;

    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', String(x));
    rect.setAttribute('y', String(y));
    rect.setAttribute('width', String(barWidth));
    rect.setAttribute('height', String(height));
    rect.setAttribute('rx', '6');
    rect.setAttribute('fill', item.color);
    svg.appendChild(rect);

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', String(x + barWidth / 2));
    label.setAttribute('y', '200');
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('class', 'axis-label');
    label.textContent = item.label;
    svg.appendChild(label);

    const value = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    value.setAttribute('x', String(x + barWidth / 2));
    value.setAttribute('y', String(y - 8));
    value.setAttribute('text-anchor', 'middle');
    value.setAttribute('class', 'axis-label');
    value.textContent = String(item.value);
    svg.appendChild(value);
  });
}

function renderThroughputChart(data) {
  const svg = elements.throughputChart;
  svg.innerHTML = '';

  if (!data.length) {
    svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" class="axis-label">No data</text>';
    return;
  }

  const maxValue = Math.max(1, ...data.map((point) => point.value));
  const width = 360;
  const height = 200;
  const padding = 28;

  const linePoints = data.map((point, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(1, data.length - 1);
    const y = height - padding - (point.value / maxValue) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  polyline.setAttribute('points', linePoints);
  polyline.setAttribute('class', 'line');
  svg.appendChild(polyline);

  data.forEach((point, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(1, data.length - 1);
    const y = height - padding - (point.value / maxValue) * (height - padding * 2);

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', String(x));
    circle.setAttribute('cy', String(y));
    circle.setAttribute('r', '4');
    circle.setAttribute('class', 'point');
    svg.appendChild(circle);

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', String(x));
    label.setAttribute('y', String(height - 6));
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('class', 'axis-label');
    label.textContent = point.label.split('-').slice(0, 2).join('-');
    svg.appendChild(label);
  });
}

function renderRequestsTable(data) {
  if (!data.length) {
    elements.requestsTable.innerHTML = '<div class="empty-state">No request data available.</div>';
    return;
  }

  const rows = data.map((request) => `
    <tr>
      <td>${escapeHtml(request.id)}</td>
      <td>${escapeHtml(String(request.count))}</td>
      <td>${escapeHtml((request.items || []).map((item) => item.id).join(', ') || '—')}</td>
    </tr>
  `).join('');

  elements.requestsTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Request</th>
          <th>Work item count</th>
          <th>Items</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderWorkItemsTable(data) {
  if (!data.length) {
    elements.workItemsTable.innerHTML = '<div class="empty-state">No work items available.</div>';
    return;
  }

  const rows = data.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td>${escapeHtml(item.type || 'unknown')}</td>
      <td><span class="badge ${escapeHtml(item.status || 'new')}">${escapeHtml(item.status || 'new')}</span></td>
      <td>${escapeHtml(item.planStatus || 'null')}</td>
      <td>${escapeHtml(item.request || '')}</td>
    </tr>
  `).join('');

  elements.workItemsTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Id</th>
          <th>Type</th>
          <th>Status</th>
          <th>Plan status</th>
          <th>Request</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderTaskTable(data) {
  if (!data.length) {
    elements.tasksTable.innerHTML = '<div class="empty-state">No task data available.</div>';
    return;
  }

  const rows = data.slice(0, 40).map((task) => `
    <tr>
      <td>${escapeHtml(task.workItemId || '')}</td>
      <td>${escapeHtml(task.id || '')}</td>
      <td>${escapeHtml(task.phase || '')}</td>
      <td>${escapeHtml(task.owner || '')}</td>
      <td><span class="badge ${escapeHtml(task.state || 'not-started')}">${escapeHtml(task.state || 'not-started')}</span></td>
    </tr>
  `).join('');

  elements.tasksTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Work item</th>
          <th>Task</th>
          <th>Phase</th>
          <th>Owner</th>
          <th>State</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderBlockedTable(data) {
  if (!data.length) {
    elements.blockedTable.innerHTML = '<div class="empty-state">No blocked work items.</div>';
    return;
  }

  const rows = data.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td>${escapeHtml(item.type || 'unknown')}</td>
      <td>${escapeHtml(item.request || '')}</td>
    </tr>
  `).join('');

  elements.blockedTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Id</th>
          <th>Type</th>
          <th>Request</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderEscalationsTable(data) {
  if (!data.length) {
    elements.escalationsTable.innerHTML = '<div class="empty-state">No escalation events recorded.</div>';
    return;
  }

  const rows = data.map((item) => `
    <tr>
      <td>${escapeHtml(item.workItemId || '')}</td>
      <td>${escapeHtml(item.taskId || '—')}</td>
      <td>${escapeHtml(item.requirement || '')}</td>
      <td>${escapeHtml(String(item.attempts || 0))}</td>
    </tr>
  `).join('');

  elements.escalationsTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Work item</th>
          <th>Task</th>
          <th>Requirement</th>
          <th>Attempts</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

loadDashboard();
