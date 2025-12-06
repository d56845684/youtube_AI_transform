const bookingForm = document.getElementById("booking-form");
const linkPreview = document.getElementById("link-preview");
const timeline = document.getElementById("timeline");
const bookingTable = document.querySelector("#booking-table tbody");
const adminTable = document.querySelector("#admin-table tbody");
const adminStatus = document.getElementById("admin-status");
const adminPill = document.getElementById("admin-pill");
const adminStats = document.getElementById("admin-stats");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

const sampleAvailabilities = [
  { teacher: "Chloe Chen", weekday: "Mon", window: "10:00 - 12:00" },
  { teacher: "Daniel Wu", weekday: "Wed", window: "14:00 - 16:00" },
  { teacher: "Hana Sato", weekday: "Fri", window: "09:00 - 11:00" },
  { teacher: "Luis García", weekday: "Sat", window: "08:00 - 10:00" },
];

const sampleBookings = [
  {
    student: "Student A",
    teacher: "Chloe Chen",
    platform: "Google Meet",
    time: "Mon 10:00",
    status: "已確認",
  },
  {
    student: "Student B",
    teacher: "Daniel Wu",
    platform: "VOOM",
    time: "Wed 15:00",
    status: "待上課",
  },
  {
    student: "Student C",
    teacher: "Hana Sato",
    platform: "Google Meet",
    time: "Fri 09:00",
    status: "已完成",
  },
];

function setActivePage(target) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.nav === target);
  });

  document.querySelectorAll(".page").forEach((page) => {
    page.classList.toggle("active", page.dataset.page === target);
  });
}

document.querySelectorAll("[data-nav]").forEach((tab) => {
  tab.addEventListener("click", () => setActivePage(tab.dataset.nav));
});

function renderTimeline() {
  if (!timeline) return;
  timeline.innerHTML = sampleAvailabilities
    .map(
      (slot) => `
      <div class="timeline-step">
        <strong>${slot.teacher}</strong> • ${slot.weekday} • ${slot.window}
        <div class="tag-row">
          <span class="tag">Realtime sync</span>
          <span class="tag">Bookable</span>
        </div>
      </div>
    `
    )
    .join("");
}

function renderBookings(targetTable, data) {
  if (!targetTable) return;
  targetTable.innerHTML = data
    .map(
      (item) => `
        <tr>
          <td>${item.student}</td>
          <td>${item.teacher}</td>
          <td>${item.time}</td>
          <td>${item.platform}</td>
          <td><a href="#">${buildConferenceLink(item.teacher, item.student, item.platform)}</a></td>
        </tr>
      `
    )
    .join("");
}

function renderAdminBookings(filter) {
  if (!adminTable) return;
  const filtered = sampleBookings.filter((booking) => {
    if (filter.scope === "student") {
      return booking.student.toLowerCase().includes(filter.keyword);
    }
    if (filter.scope === "teacher") {
      return booking.teacher.toLowerCase().includes(filter.keyword);
    }
    return (
      booking.student.toLowerCase().includes(filter.keyword) ||
      booking.teacher.toLowerCase().includes(filter.keyword)
    );
  });

  adminTable.innerHTML = filtered
    .map(
      (item) => `
        <tr>
          <td>${item.student}</td>
          <td>${item.teacher}</td>
          <td>${item.platform}</td>
          <td>${item.status}</td>
          <td><a href="#">${buildConferenceLink(item.teacher, item.student, item.platform)}</a></td>
        </tr>
      `
    )
    .join("");

  if (adminPill) {
    const scopeLabel = filter.scope === "all" ? "顯示全部" : `篩選：${filter.scope}`;
    adminPill.textContent = scopeLabel;
  }
  if (adminStatus) {
    adminStatus.textContent = `目前共 ${filtered.length} 筆，關鍵字「${filter.keyword || "無"}」`;
  }
  renderAdminStats(filtered);
}

function renderAdminStats(list) {
  if (!adminStats) return;
  const total = list.length;
  const byPlatform = list.reduce(
    (acc, item) => {
      acc[item.platform] = (acc[item.platform] || 0) + 1;
      return acc;
    },
    {}
  );

  adminStats.innerHTML = `
    <div class="stat-card">
      <strong>總預約</strong>
      <span>${total} 筆</span>
    </div>
    <div class="stat-card">
      <strong>Google Meet</strong>
      <span>${byPlatform["Google Meet"] || 0} 筆</span>
    </div>
    <div class="stat-card">
      <strong>VOOM</strong>
      <span>${byPlatform["VOOM"] || 0} 筆</span>
    </div>
  `;
}

function buildConferenceLink(teacherId, studentId, platform) {
  const platformDomain = platform === "Google Meet" ? "meet.google.com" : "voom.com";
  const timestamp = Math.floor(Date.now() / 1000);
  return `https://${platformDomain}/${teacherId}-${studentId}-${timestamp}`;
}

if (bookingForm) {
  bookingForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(bookingForm);
    const teacherId = formData.get("teacherId") || "18";
    const studentId = formData.get("studentId") || "42";
    const platform = formData.get("platform");

    const link = buildConferenceLink(teacherId, studentId, platform);
    linkPreview.textContent = link;
    linkPreview.classList.add("status-pill");

    sampleBookings.unshift({
      student: studentId,
      teacher: teacherId,
      platform,
      time: "即將開始",
      status: "待確認",
    });
    renderBookings(bookingTable, sampleBookings);
    renderAdminBookings({ scope: "all", keyword: "" });
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    const statusEl = document.getElementById("login-status");
    statusEl.textContent = `已送出 /auth/token，角色：${formData.get("role")}`;
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(registerForm);
    const statusEl = document.getElementById("register-status");
    statusEl.textContent = `已送出 /auth/register，Email：${formData.get("email")}`;
  });
}

const adminFilterForm = document.getElementById("admin-filter");
if (adminFilterForm) {
  adminFilterForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(adminFilterForm);
    const scope = formData.get("scope");
    const keyword = (formData.get("keyword") || "").toLowerCase();
    renderAdminBookings({ scope, keyword });
  });
}

renderTimeline();
renderBookings(bookingTable, sampleBookings);
renderAdminBookings({ scope: "all", keyword: "" });
setActivePage("auth");
