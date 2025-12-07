const bookingForm = document.getElementById("booking-form");
const linkPreview = document.getElementById("link-preview");
const timeline = document.getElementById("timeline");
const timelineStatus = document.getElementById("timeline-status");
const bookingTable = document.querySelector("#booking-table tbody");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const bookingStatus = document.getElementById("booking-status");
const selectedSlotView = document.getElementById("selected-slot");
const loadAvailabilityBtn = document.getElementById("load-availability");

const sampleAvailabilities = [
  { id: 1, teacher: "Chloe Chen", weekday: "Mon", window: "10:00 - 12:00", is_booked: 0 },
  { id: 2, teacher: "Daniel Wu", weekday: "Wed", window: "14:00 - 16:00", is_booked: 0 },
  { id: 3, teacher: "Hana Sato", weekday: "Fri", window: "09:00 - 11:00", is_booked: 0 },
  { id: 4, teacher: "Luis García", weekday: "Sat", window: "08:00 - 10:00", is_booked: 0 },
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

const API_BASE =
  window.BACKEND_API_BASE ||
  (window.location.origin.match(/:\d+$/)
    ? window.location.origin.replace(/:\d+$/, ":8000")
    : `${window.location.protocol}//${window.location.hostname}:8000`);

let authToken = null;
let currentUser = null;
let bookingData = [];
let selectedSlot = null;

function setStatus(target, message, isError = false) {
  if (!target) return;
  target.textContent = message;
  target.classList.toggle("error", isError);
}

async function apiFetch(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  if (!response.ok) {
    const detail = isJson ? await response.json() : await response.text();
    const errorMessage = typeof detail === "string" ? detail : detail?.detail || "Unknown error";
    throw new Error(errorMessage);
  }
  return isJson ? response.json() : response.text();
}

function formatTimeRange(slot) {
  if (!slot) return "";
  if (slot.window) return slot.window;
  const start = slot.start_time ? slot.start_time.toString().slice(0, 5) : "";
  const end = slot.end_time ? slot.end_time.toString().slice(0, 5) : "";
  return `${start} - ${end}`;
}

function normalizeBooking(item) {
  if (!item) return null;
  if (item.link || item.time || item.student) {
    return {
      student: item.student ?? item.student_id ?? "Unknown",
      teacher: item.teacher ?? item.teacher_id ?? "Unknown",
      platform: item.platform,
      time: item.time ?? (item.availability ? `${item.availability.weekday} ${formatTimeRange(item.availability)}` : "預約時間待確認"),
      status: item.status ?? "已建立",
      link: item.link ?? item.conference_link ?? buildConferenceLink(item.teacher, item.student, item.platform),
    };
  }

  return {
    student: item.student_id ?? "Unknown",
    teacher: item.teacher_id ?? "Unknown",
    platform: item.platform,
    time: item.availability ? `${item.availability.weekday} ${formatTimeRange(item.availability)}` : new Date(item.reserved_at).toLocaleString(),
    status: "已建立",
    link: item.conference_link,
  };
}

function buildConferenceLink(teacherId, studentId, platform) {
  const platformDomain = platform === "Google Meet" ? "meet.google.com" : "voom.com";
  const timestamp = Math.floor(Date.now() / 1000);
  return `https://${platformDomain}/${teacherId}-${studentId}-${timestamp}`;
}

function renderTimeline(list = sampleAvailabilities, fromApi = false) {
  if (!timeline) return;
  timeline.innerHTML =
    list
      .map(
        (slot) => `
      <div class="timeline-step" data-slot-id="${slot.id || ""}">
        <div class="timeline-meta">
          <strong>${slot.teacher || `Teacher #${slot.teacher_id}`}</strong> • ${slot.weekday} • ${formatTimeRange(slot)}
          <div class="tag-row">
            <span class="tag">${fromApi ? "Live API" : "Sample"}</span>
            ${slot.id ? `<span class="tag">ID ${slot.id}</span>` : ""}
            <span class="tag ${slot.is_booked ? "tag-muted" : ""}">${slot.is_booked ? "已被預約" : "可預約"}</span>
          </div>
        </div>
        <button class="ghost" data-action="select-slot" ${slot.is_booked ? "disabled" : ""}>選擇</button>
      </div>
    `
      )
      .join("") || "<p>沒有可用時段</p>";

  timeline.querySelectorAll("[data-action=select-slot]").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      const wrapper = event.target.closest(".timeline-step");
      const id = wrapper?.dataset.slotId;
      const slot = list.find((item) => `${item.id}` === id);
      selectSlot(slot || list[0]);
    });
  });
}

function renderBookings(targetTable, data) {
  if (!targetTable) return;
  const normalized = data.map(normalizeBooking).filter(Boolean);
  targetTable.innerHTML = normalized
    .map(
      (item) => `
        <tr>
          <td>${item.student}</td>
          <td>${item.teacher}</td>
          <td>${item.time}</td>
          <td>${item.platform}</td>
          <td><a href="${item.link}" target="_blank" rel="noopener">${item.link}</a></td>
        </tr>
      `
    )
    .join("");
}

function renderAllBookings() {
  renderBookings(bookingTable, bookingData);
}

function filterStudentBookings(data) {
  if (!currentUser || currentUser.role !== "student") return data;
  return data.filter((item) => {
    const normalized = normalizeBooking(item);
    return normalized?.student?.toString().toLowerCase().includes(currentUser.email.toLowerCase());
  });
}

async function refreshBookings() {
  if (!bookingTable) return;
  if (!authToken) {
    bookingData = sampleBookings.map((item) => ({ ...normalizeBooking(item), status: item.status }));
    renderAllBookings();
    setStatus(bookingStatus, "未登入，顯示示範預約");
    return;
  }

  try {
    const bookings = await apiFetch("/bookings");
    const filtered = filterStudentBookings(bookings);
    bookingData = filtered.map((item) => ({ ...normalizeBooking(item), status: item.status ?? "已建立" }));
    renderAllBookings();
    setStatus(bookingStatus, `已載入 ${bookingData.length} 筆預約`);
  } catch (error) {
    setStatus(bookingStatus, `讀取預約失敗：${error.message}，顯示示範資料`, true);
    bookingData = sampleBookings.map((item) => ({ ...normalizeBooking(item), status: item.status }));
    renderAllBookings();
  }
}

async function loadAvailability(teacherId) {
  if (!teacherId) {
    renderTimeline(sampleAvailabilities, false);
    setStatus(timelineStatus, "請先輸入 Teacher ID", true);
    return;
  }

  try {
    const availability = await apiFetch(`/teachers/${teacherId}/availability`);
    if (!availability.length) {
      renderTimeline(sampleAvailabilities, false);
      setStatus(timelineStatus, "無可用時段，顯示示範資料", true);
      return;
    }
    renderTimeline(availability, true);
    setStatus(timelineStatus, `已載入 Teacher #${teacherId} 的 ${availability.length} 筆時段`);
  } catch (error) {
    renderTimeline(sampleAvailabilities, false);
    setStatus(timelineStatus, `載入失敗：${error.message}，改用示範資料`, true);
  }
}

function setActivePage(target) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.nav === target);
  });

  document.querySelectorAll(".page").forEach((page) => {
    page.classList.toggle("active", page.dataset.page === target);
  });
}

function selectSlot(slot) {
  if (!slot) return;
  selectedSlot = slot;
  if (selectedSlotView) {
    selectedSlotView.textContent = `${slot.weekday} ${formatTimeRange(slot)} ｜ ${slot.teacher || "教師"}（ID ${slot.id || "N/A"}）`;
    selectedSlotView.classList.add("active");
  }
  if (bookingForm) {
    const teacherInput = bookingForm.querySelector("input[name=\"teacherId\"]");
    const availabilityInput = bookingForm.querySelector("input[name=\"availabilityId\"]");
    if (teacherInput && (slot.teacher_id || teacherInput.value === "")) {
      teacherInput.value = slot.teacher_id || teacherInput.value;
    }
    if (availabilityInput && slot.id) {
      availabilityInput.value = slot.id;
    }
  }
}

document.querySelectorAll("[data-nav]").forEach((tab) => {
  tab.addEventListener("click", () => {
    setActivePage(tab.dataset.nav);
    if (tab.dataset.nav === "booking") {
      const teacherInput = bookingForm?.querySelector("input[name=\"teacherId\"]");
      loadAvailability(teacherInput?.value || "");
    }
  });
});

if (bookingForm) {
  bookingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(bookingForm);
    const studentId = formData.get("studentId") || "";
    const teacherId = formData.get("teacherId") || "";
    const availabilityId = Number(formData.get("availabilityId"));
    const platform = formData.get("platform");

    if (!authToken) {
      setStatus(linkPreview, "請先登入取得 Token 後再預約", true);
      return;
    }
    if (!availabilityId) {
      setStatus(linkPreview, "請輸入有效的 Availability ID", true);
      return;
    }

    try {
      const booking = await apiFetch("/bookings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ availability_id: availabilityId, platform }),
      });
      const normalized = normalizeBooking(booking);
      bookingData.unshift({ ...normalized, student: normalized.student || studentId, teacher: normalized.teacher || teacherId });
      renderAllBookings();
      setStatus(linkPreview, `預約成功！會議連結：${normalized.link}`);
      linkPreview.classList.add("status-pill");
    } catch (error) {
      setStatus(linkPreview, `預約失敗：${error.message}`, true);
    }
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    const email = formData.get("email");
    const password = formData.get("password");

    try {
      const payload = new URLSearchParams();
      payload.set("username", email);
      payload.set("password", password);
      const token = await apiFetch("/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: payload,
      });
      authToken = token.access_token;
      setStatus(document.getElementById("login-status"), "登入成功，已取得存取權杖");

      currentUser = await apiFetch("/users/me");
      setStatus(document.getElementById("login-status"), `使用者：${currentUser.email}（${currentUser.role}）`);
      setActivePage("booking");
      await refreshBookings();
    } catch (error) {
      setStatus(document.getElementById("login-status"), `登入失敗：${error.message}`, true);
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(registerForm);
    const payload = {
      email: formData.get("email"),
      password: formData.get("password"),
      full_name: formData.get("fullName"),
      role: formData.get("role"),
    };

    try {
      const result = await apiFetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setStatus(
        document.getElementById("register-status"),
        `註冊成功：${result.email}（${result.role}），請返回登入`,
      );
    } catch (error) {
      setStatus(document.getElementById("register-status"), `註冊失敗：${error.message}`, true);
    }
  });
}

if (loadAvailabilityBtn) {
  loadAvailabilityBtn.addEventListener("click", () => {
    const teacherInput = bookingForm?.querySelector("input[name=\"teacherId\"]");
    loadAvailability(teacherInput?.value || "");
  });
}

renderTimeline(sampleAvailabilities, false);
bookingData = sampleBookings.map((item) => ({ ...normalizeBooking(item), status: item.status }));
renderAllBookings();
setActivePage("auth");

const teacherInput = bookingForm?.querySelector("input[name=\"teacherId\"]");
if (teacherInput) {
  teacherInput.addEventListener("change", () => loadAvailability(teacherInput.value));
  loadAvailability(teacherInput.value);
}
