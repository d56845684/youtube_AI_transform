const bookingForm = document.getElementById("booking-form");
const linkPreview = document.getElementById("link-preview");
const timeline = document.getElementById("timeline");
const timelineStatus = document.getElementById("timeline-status");
const bookingTable = document.querySelector("#booking-table tbody");
const teacherBookingTable = document.querySelector("#teacher-booking-table tbody");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const bookingStatus = document.getElementById("booking-status");
const teacherBookingStatus = document.getElementById("teacher-booking-status");
const selectedSlotView = document.getElementById("selected-slot");
const loadAvailabilityBtn = document.getElementById("load-availability");
const teacherIdInput = document.getElementById("teacher-id-input");
const teacherNameInput = document.getElementById("teacher-name-input");
const teacherTools = document.getElementById("teacher-tools");
const teacherToolsStatus = document.getElementById("teacher-tools-status");
const teacherAvailabilityForm = document.getElementById("teacher-availability-form");
const teacherDateInput = document.getElementById("teacher-date");
const teacherWeekdayInput = document.getElementById("teacher-weekday");
const teacherAvailabilityList = document.getElementById("teacher-availability-list");
const teacherAvailabilityLabel = document.getElementById("teacher-availability-label");
const teacherAvailabilityStatus = document.getElementById("teacher-availability-status");
const studentOnlySections = document.querySelectorAll(".student-only");
const cancelModal = document.getElementById("cancel-modal");
const cancelReasonInput = document.getElementById("cancel-reason");
const confirmCancelBtn = document.getElementById("confirm-cancel");
const cancelDismissButtons = document.querySelectorAll("[data-dismiss=cancel]");

const sampleAvailabilities = [
  { id: 1, teacher: "Chloe Chen", weekday: "Mon", window: "10:00 - 12:00", is_booked: 0 },
  { id: 2, teacher: "Daniel Wu", weekday: "Wed", window: "14:00 - 16:00", is_booked: 0 },
  { id: 3, teacher: "Hana Sato", weekday: "Fri", window: "09:00 - 11:00", is_booked: 0 },
  { id: 4, teacher: "Luis García", weekday: "Sat", window: "08:00 - 10:00", is_booked: 0 },
];

const sampleBookings = [
  {
    id: 1,
    student: "Student A",
    teacher: "Chloe Chen",
    platform: "Google Meet",
    time: "Mon 10:00",
    status: "成功",
  },
  {
    id: 2,
    student: "Student B",
    teacher: "Daniel Wu",
    platform: "Zoom",
    time: "Wed 15:00",
    meeting_id: "987654321",
    status: "成功",
  },
  {
    id: 3,
    student: "Student C",
    teacher: "Hana Sato",
    platform: "Google Meet",
    time: "Fri 09:00",
    status: "取消",
    status_desc: "示範：臨時有事",
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
let teacherDirectory = [];
let pendingCancelBookingId = null;

function setStatus(target, message, isError = false) {
  if (!target) return;
  target.textContent = message;
  target.classList.toggle("error", isError);
}

function formatTimeValue(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value.toString().slice(0, 5);
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeAttribute(value) {
  if (value === undefined || value === null) return "";
  return value.toString().replaceAll('"', "&quot;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function formatDateValue(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value.toString();
  }
  return date.toLocaleDateString(undefined, { year: "numeric", month: "2-digit", day: "2-digit" });
}

function deriveWeekdayLabel(dateValue) {
  if (!dateValue) return "-";
  const parsed = new Date(dateValue);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleDateString("en-US", { weekday: "short" });
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
  const start = slot.start_time ? formatTimeValue(slot.start_time) : "";
  const end = slot.end_time ? formatTimeValue(slot.end_time) : "";
  return `${start} - ${end}`;
}

function describeAvailability(slot) {
  if (!slot) return "預約時間待確認";
  const dateLabel = slot.availability_date
    ? `${formatDateValue(slot.availability_date)} (${slot.weekday || ""})`
    : slot.weekday || "未指定日期";
  return `${dateLabel} ${formatTimeRange(slot)}`.trim();
}

function resolveDriveLink(source) {
  if (!source) return "";
  return (
    source.drive_share_link ||
    source.driveShareLink ||
    source.drive_link ||
    source.driveLink ||
    ""
  );
}

function openCancelModal(bookingId, defaultReason = "學生取消預約") {
  if (!cancelModal) return;
  pendingCancelBookingId = bookingId;
  cancelModal.classList.add("show");
  if (cancelReasonInput) {
    cancelReasonInput.value = defaultReason || "";
    cancelReasonInput.focus();
  }
}

function closeCancelModal() {
  pendingCancelBookingId = null;
  cancelModal?.classList.remove("show");
  if (cancelReasonInput) cancelReasonInput.value = "";
}

cancelDismissButtons.forEach((btn) => {
  btn.addEventListener("click", closeCancelModal);
});

if (confirmCancelBtn) {
  confirmCancelBtn.addEventListener("click", async () => {
    if (!pendingCancelBookingId) {
      closeCancelModal();
      return;
    }

    const reason = cancelReasonInput?.value?.trim() || "學生取消預約";
    try {
      await apiFetch(`/bookings/${pendingCancelBookingId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status_desc: reason }),
      });
      setStatus(bookingStatus, "預約已取消");
      await refreshBookings();
    } catch (error) {
      setStatus(bookingStatus, `取消失敗：${error.message}`, true);
    }
    closeCancelModal();
  });
}

if (cancelModal) {
  cancelModal.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeCancelModal();
    }
  });
}

function normalizeBooking(item) {
  if (!item) return null;

  const studentName =
    item.student?.full_name || item.student_full_name || item.student || item.student_id || "Unknown";
  const teacherName =
    item.teacher?.full_name || item.teacher_full_name || item.teacher || item.teacher_id || "Unknown";

  const zoomRecording = item.zoom_recording || item.zoomRecording;
  const meetingId = zoomRecording?.meeting_id || item.meeting_id || item.meetingId || "";
  const driveLink = resolveDriveLink(zoomRecording) || item.drive_link || "";

  const hasNestedUsers =
    (item.student && typeof item.student === "object") ||
    (item.teacher && typeof item.teacher === "object") ||
    item.availability;

  if (hasNestedUsers || item.conference_link || item.reserved_at) {
    const timeLabel =
      (item.availability && describeAvailability(item.availability)) ||
      (item.reserved_at && new Date(item.reserved_at).toLocaleString()) ||
      item.time ||
      "預約時間待確認";

    return {
      id: item.id,
      student_id: item.student_id,
      teacher_id: item.teacher_id,
      student: studentName,
      teacher: teacherName,
      platform: item.platform || "Google Meet",
      time: timeLabel,
      status: item.status || "成功",
      status_desc: item.status_desc || "",
      link:
        item.conference_link ||
        item.link ||
        buildConferenceLink(item.teacher_id || teacherName, item.student_id || studentName, item.platform),
      meeting_id: meetingId,
      drive_link: driveLink,
      zoom_recording: zoomRecording,
    };
  }

  return {
    id: item.id,
    student_id: item.student_id,
    teacher_id: item.teacher_id,
    student: studentName,
    teacher: teacherName,
    platform: item.platform,
    time: item.time ?? describeAvailability(item.availability),
    status: item.status ?? "成功",
    status_desc: item.status_desc || "",
    link: item.link ?? item.conference_link ?? buildConferenceLink(item.teacher, item.student, item.platform),
    meeting_id: meetingId,
    drive_link: driveLink,
    zoom_recording: zoomRecording,
  };
}

function buildConferenceLink(teacherId, studentId, platform) {
  const platformDomain =
    platform === "Google Meet" ? "meet.google.com" : platform === "Zoom" ? "zoom.us" : "voom.com";
  const timestamp = Math.floor(Date.now() / 1000);
  return `https://${platformDomain}/${teacherId}-${studentId}-${timestamp}`;
}

function renderTimeline(list = sampleAvailabilities, fromApi = false, target = timeline, selectable = true) {
  if (!target) return;
  const activeList = Array.isArray(list) ? list.filter((slot) => !slot.deleted_at) : [];
  target.innerHTML =
    activeList
      .map((slot) => {
        const dateLabel = slot.availability_date
          ? `${formatDateValue(slot.availability_date)} (${slot.weekday || ""})`
          : slot.weekday || "未指定日期";
        const teacherName = slot.teacher?.full_name || slot.teacher_full_name || slot.teacher || `Teacher #${slot.teacher_id}`;
        const isBooked = Boolean(slot.is_booked);
        return `
        <div class="timeline-step" data-slot-id="${slot.id || ""}">
          <div class="timeline-meta">
            <strong>${teacherName}</strong> • ${dateLabel} • ${formatTimeRange(slot)}
            <div class="tag-row">
              <span class="tag">${fromApi ? "Live API" : "Sample"}</span>
              ${slot.id ? `<span class="tag">ID ${slot.id}</span>` : ""}
              <span class="tag ${isBooked ? "tag-muted" : ""}">${isBooked ? "已預約" : "可預約"}</span>
            </div>
          </div>
          ${selectable ? `<button class="ghost ${isBooked ? "booked" : ""}" data-action="select-slot" ${isBooked ? "disabled" : ""}>選擇</button>` : ""}
        </div>
      `;
      })
      .join("") || "<p>沒有可用時段</p>";

  if (!selectable) return;
  target.querySelectorAll("[data-action=select-slot]").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      const wrapper = event.target.closest(".timeline-step");
      const id = wrapper?.dataset.slotId;
      const slot = activeList.find((item) => `${item.id}` === id);
      selectSlot(slot || activeList[0]);
    });
  });
}

function renderBookings(targetTable, data) {
  if (!targetTable) return;
  const normalized = data.map(normalizeBooking).filter(Boolean);
  const isStudentTable = targetTable === bookingTable;
  targetTable.innerHTML = normalized
    .map((item) => {
      const canCancel =
        isStudentTable &&
        currentUser?.role === "student" &&
        `${item.student_id}` === `${currentUser?.id}` &&
        item.status !== "取消";
      const statusBadge = `<span class="tag ${item.status === "取消" ? "tag-muted" : ""}">${item.status || "成功"}</span>`;
      const statusDesc = item.status_desc || "";
      const defaultReason = statusDesc || "學生取消預約";
      const actionCell = isStudentTable
        ? `<button class="ghost" data-action="cancel-booking" data-booking-id="${item.id}" data-default-reason="${escapeAttribute(defaultReason)}" ${canCancel ? "" : "disabled"}>${item.status === "取消" ? "已取消" : "取消預約"}</button>`
        : "";
      const recordingCell = !isStudentTable
        ? `<div class="stacked">
            ${
              item.platform === "Zoom"
                ? item.drive_link
                  ? `<a class="muted" href="${escapeAttribute(item.drive_link)}" target="_blank" rel="noopener">Drive 連結</a>`
                  : `<button class="ghost" data-action="fetch-recording" data-booking-id="${item.id}" data-meeting-id="${escapeAttribute(item.meeting_id || "")}">取得錄影</button>`
                : "-"
            }
            ${item.meeting_id ? `<span class="muted">Meeting ID: ${escapeAttribute(item.meeting_id)}</span>` : ""}
          </div>`
        : "";
      return `
        <tr>
          <td>${item.student}</td>
          <td>${item.teacher}</td>
          <td>${item.time}</td>
          <td>${item.platform}</td>
          <td>${statusBadge}</td>
          <td>${statusDesc || "-"}</td>
          <td><a href="${item.link}" target="_blank" rel="noopener">${item.link}</a></td>
          ${recordingCell ? `<td>${recordingCell}</td>` : ""}
          ${isStudentTable ? `<td>${actionCell}</td>` : ""}
        </tr>
      `;
    })
    .join("");

  if (isStudentTable) {
    targetTable.querySelectorAll("[data-action=cancel-booking]").forEach((btn) => {
      btn.addEventListener("click", async (event) => {
        const bookingId = event.currentTarget.dataset.bookingId;
        if (!bookingId) return;
        const defaultReason = event.currentTarget.dataset.defaultReason || "學生取消預約";
        openCancelModal(bookingId, defaultReason);
      });
    });
  } else {
    targetTable.querySelectorAll("[data-action=fetch-recording]").forEach((btn) => {
      btn.addEventListener("click", async (event) => {
        const bookingId = event.currentTarget.dataset.bookingId;
        const meetingId = event.currentTarget.dataset.meetingId;
        const defaultEmail = currentUser?.email || "";
        const shareEmail = prompt("輸入要分享錄影檔案的 Email", defaultEmail);
        if (!bookingId || !shareEmail) return;

        try {
          const payload = { share_email: shareEmail };
          if (meetingId) payload.meeting_id = meetingId;
          const record = await apiFetch(`/bookings/${bookingId}/zoom-recording`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          const driveLink = resolveDriveLink(record);
          setStatus(
            teacherBookingStatus,
            `錄影檔案已上傳到雲端：${record.drive_share_link || record.drive_file_id || "完成"}`
          );
          if (driveLink) {
            const idx = bookingData.findIndex((item) => `${item?.id}` === `${bookingId}`);
            if (idx >= 0) {
              const existing = bookingData[idx] || {};
              const updatedRecording = {
                ...(existing.zoom_recording || {}),
                ...record,
                drive_link: driveLink,
                drive_share_link: driveLink,
              };
              bookingData[idx] = { ...existing, drive_link: driveLink, zoom_recording: updatedRecording };
              renderAllBookings();
            }
          }
        } catch (error) {
          setStatus(teacherBookingStatus, `取得錄影失敗：${error.message}`, true);
        }
      });
    });
  }
}

function renderAllBookings() {
  const studentView = currentUser?.role === "student" ? filterStudentBookings(bookingData) : bookingData;
  renderBookings(bookingTable, studentView);
  renderBookings(teacherBookingTable, bookingData);
}

function filterStudentBookings(data) {
  if (!currentUser || currentUser.role !== "student") return data;
  return data.filter((item) => {
    if (item && item.student_id !== undefined && item.student_id !== null) {
      return `${item.student_id}` === `${currentUser.id}`;
    }

    const normalized = normalizeBooking(item);
    return normalized?.student?.toString().toLowerCase().includes(currentUser.email.toLowerCase());
  });
}

async function refreshBookings() {
  if (!bookingTable && !teacherBookingTable) return;
  if (!authToken) {
    bookingData = sampleBookings;
    renderAllBookings();
    setStatus(bookingStatus, "未登入，顯示示範預約");
    setStatus(teacherBookingStatus, "需以教師身分登入", true);
    return;
  }

  try {
    const bookings = await apiFetch("/bookings");
    bookingData = bookings;
    renderAllBookings();
    const studentViewLength =
      currentUser?.role === "student" ? filterStudentBookings(bookings).length : bookings.length;
    setStatus(bookingStatus, `已載入 ${studentViewLength} 筆預約`);
    if (teacherBookingStatus) {
      setStatus(teacherBookingStatus, `教師已載入 ${bookings.length} 筆課程/會議`);
    }
  } catch (error) {
    setStatus(bookingStatus, `讀取預約失敗：${error.message}，顯示示範資料`, true);
    bookingData = sampleBookings;
    renderAllBookings();
    if (teacherBookingStatus) {
      setStatus(teacherBookingStatus, `教師列表載入失敗：${error.message}，顯示示範資料`, true);
    }
  }
}

async function loadAvailability(teacherId) {
  const trimmedId = teacherId?.toString().trim();
  if (!trimmedId) {
    renderTimeline(sampleAvailabilities, false);
    setStatus(timelineStatus, "請先輸入教師姓名或 ID", true);
    return;
  }

  try {
    const availability = await apiFetch(`/teachers/${trimmedId}/availability`);
    if (!availability.length) {
      renderTimeline(sampleAvailabilities, false);
      setStatus(timelineStatus, "無可用時段，顯示示範資料", true);
      return;
    }
    renderTimeline(availability, true);
    const teacherName = availability[0]?.teacher?.full_name;
    const label = teacherName ? `${teacherName}（ID ${trimmedId}）` : `Teacher #${trimmedId}`;
    setStatus(timelineStatus, `已載入 ${label} 的 ${availability.length} 筆時段`);
  } catch (error) {
    renderTimeline(sampleAvailabilities, false);
    setStatus(timelineStatus, `載入失敗：${error.message}，改用示範資料`, true);
  }
}

function renderTeacherOptions(list) {
  if (!teacherNameInput) return;
  const selected = teacherNameInput.value;
  teacherNameInput.innerHTML =
    '<option value="">選擇老師（自動帶入 ID）</option>' +
    list.map((teacher) => `<option value="${teacher.id}">${teacher.full_name}</option>`).join("");
  if (selected) {
    teacherNameInput.value = selected;
  }
}

function findTeacherIdByName(name) {
  if (!name) return null;
  const normalized = name.toString().trim();
  if (/^\d+$/.test(normalized)) return normalized;
  const lower = normalized.toLowerCase();
  const match = teacherDirectory.find((teacher) => teacher.full_name.toLowerCase() === lower);
  return match?.id ?? null;
}

async function refreshTeacherDirectory(query = "") {
  try {
    const url = query ? `/teachers?search=${encodeURIComponent(query)}` : "/teachers";
    const teachers = await apiFetch(url);
    teacherDirectory = teachers;
    renderTeacherOptions(teachers);
  } catch (error) {
    setStatus(timelineStatus, `老師列表載入失敗：${error.message}`, true);
  }
}

async function refreshTeacherAvailability() {
  if (!teacherAvailabilityList) return;
  if (!authToken || !currentUser || currentUser.role !== "teacher") {
    renderTimeline(sampleAvailabilities, false, teacherAvailabilityList, false);
    setStatus(teacherAvailabilityLabel, currentUser ? "登入角色非教師" : "需教師登入", true);
    return;
  }

  try {
    const availability = await apiFetch(`/teachers/${currentUser.id}/availability`);
    renderTimeline(availability, true, teacherAvailabilityList, false);
    setStatus(teacherAvailabilityLabel, `共 ${availability.length} 筆可預約時段`);
  } catch (error) {
    renderTimeline(sampleAvailabilities, false, teacherAvailabilityList, false);
    setStatus(teacherAvailabilityLabel, `教師時段載入失敗：${error.message}，改用示範資料`, true);
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

function updateRoleUI() {
  const isTeacher = currentUser?.role === "teacher";
  if (studentOnlySections.length) {
    studentOnlySections.forEach((section) => section.classList.toggle("hidden", isTeacher));
  }
  if (teacherTools) {
    teacherTools.classList.toggle("hidden", !isTeacher);
  }
  if (teacherToolsStatus) {
    setStatus(teacherToolsStatus, isTeacher ? `教師模式：${currentUser?.email}` : "需以教師身分登入", !isTeacher && !!currentUser);
  }
  if (!isTeacher) {
    renderTimeline(sampleAvailabilities, false, teacherAvailabilityList, false);
    setStatus(teacherAvailabilityLabel, currentUser ? "登入角色非教師" : "需教師登入", true);
    setStatus(teacherBookingStatus, currentUser ? "登入角色非教師" : "需以教師身分登入", true);
    renderBookings(teacherBookingTable, bookingData);
    return;
  }

  syncTeacherInputs(currentUser?.id ? `${currentUser.id}` : teacherIdInput?.value || "");
  refreshTeacherAvailability();
}

function selectSlot(slot) {
  if (!slot) return;
  selectedSlot = slot;
  if (selectedSlotView) {
    const dateLabel = slot.availability_date
      ? `${formatDateValue(slot.availability_date)} (${slot.weekday || ""})`
      : slot.weekday;
    const teacherLabel = slot.teacher?.full_name || slot.teacher_full_name || slot.teacher || slot.teacher_id || "教師";
    selectedSlotView.textContent = `${dateLabel} ${formatTimeRange(slot)} ｜ ${teacherLabel}（ID ${slot.id || "N/A"}）`;
    selectedSlotView.classList.add("active");
  }
  if (slot.teacher_id) {
    syncTeacherInputs(`${slot.teacher_id}`);
  }
  if (bookingForm) {
    const availabilityInput = bookingForm.querySelector("input[name=\"availabilityId\"]");
    if (availabilityInput && slot.id) {
      availabilityInput.value = slot.id;
    }
  }
}

function syncTeacherInputs(value) {
  if (teacherIdInput && teacherIdInput.value !== value) {
    teacherIdInput.value = value;
  }
  const matched = teacherDirectory.find((teacher) => `${teacher.id}` === `${value}`);
  if (teacherNameInput && matched && `${teacherNameInput.value}` !== `${matched.id}`) {
    teacherNameInput.value = `${matched.id}`;
  }
}

document.querySelectorAll("[data-nav]").forEach((tab) => {
  tab.addEventListener("click", () => {
    setActivePage(tab.dataset.nav);
    updateRoleUI();
    if (tab.dataset.nav === "booking") {
      const teacherId = teacherIdInput?.value || findTeacherIdByName(teacherNameInput?.value) || "";
      loadAvailability(teacherId);
      if (currentUser?.role === "teacher") {
        refreshTeacherAvailability();
      }
    }
  });
});

if (teacherNameInput) {
  teacherNameInput.addEventListener("change", (event) => {
    const selectedId = event.target.value;
    if (selectedId) {
      syncTeacherInputs(`${selectedId}`);
      loadAvailability(selectedId);
    }
  });
}

if (bookingForm) {
  bookingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(bookingForm);
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
      bookingData.unshift(normalized);
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
      updateRoleUI();
      syncTeacherInputs(currentUser?.id ? `${currentUser.id}` : teacherIdInput?.value || "");
      setActivePage("booking");
      const teacherId = teacherIdInput?.value || "";
      loadAvailability(teacherId.trim());
      await refreshBookings();
      await refreshTeacherAvailability();
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

if (teacherAvailabilityForm) {
  teacherAvailabilityForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!currentUser || currentUser.role !== "teacher") {
      setStatus(teacherAvailabilityStatus, "僅教師可以新增可預約時段", true);
      return;
    }
    const formData = new FormData(teacherAvailabilityForm);
    const availabilityDate = formData.get("availabilityDate");
    const startValue = formData.get("startTime");
    const endValue = formData.get("endTime");
    const startDate = startValue && availabilityDate ? new Date(`${availabilityDate}T${startValue}`) : null;
    const endDate = endValue && availabilityDate ? new Date(`${availabilityDate}T${endValue}`) : null;

    if (!availabilityDate || !startDate || !endDate || Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      setStatus(teacherAvailabilityStatus, "請選擇有效的日期與時間", true);
      return;
    }
    if (startDate.toDateString() !== endDate.toDateString()) {
      setStatus(teacherAvailabilityStatus, "開始與結束時間需在同一天", true);
      return;
    }
    if (startDate >= endDate) {
      setStatus(teacherAvailabilityStatus, "請輸入有效的開始與結束時間", true);
      return;
    }

    const payload = {
      availability_date: availabilityDate,
      start_time: startValue,
      end_time: endValue,
    };

    try {
      const created = await apiFetch("/teachers/availability", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setStatus(
        teacherAvailabilityStatus,
        `已新增 ${formatDateValue(created.availability_date)} (${created.weekday}) ${formatTimeRange(created)}`,
      );
      teacherAvailabilityForm.reset();
      if (teacherDateInput) {
        teacherDateInput.value = availabilityDate;
        teacherWeekdayInput.value = deriveWeekdayLabel(availabilityDate);
      }
      syncTeacherInputs(currentUser.id ? `${currentUser.id}` : "");
      await refreshTeacherAvailability();
      if (teacherIdInput) {
        loadAvailability(teacherIdInput.value.trim());
      }
    } catch (error) {
      setStatus(teacherAvailabilityStatus, `新增失敗：${error.message}`, true);
    }
  });
}

if (loadAvailabilityBtn) {
  loadAvailabilityBtn.addEventListener("click", () => {
    const teacherId = teacherIdInput?.value || findTeacherIdByName(teacherNameInput?.value) || "";
    syncTeacherInputs(teacherId.toString().trim());
    loadAvailability(teacherId.toString().trim());
  });
}

function initializeAvailabilityDateUI() {
  if (!teacherDateInput) return;
  const todayIso = new Date().toISOString().slice(0, 10);
  if (!teacherDateInput.value) {
    teacherDateInput.value = todayIso;
  }
  if (teacherWeekdayInput) {
    teacherWeekdayInput.value = deriveWeekdayLabel(teacherDateInput.value);
  }

  teacherDateInput.addEventListener("change", () => {
    if (teacherWeekdayInput) {
      teacherWeekdayInput.value = deriveWeekdayLabel(teacherDateInput.value);
    }
  });
}

initializeAvailabilityDateUI();

refreshTeacherDirectory();

renderTimeline(sampleAvailabilities, false);
renderTimeline(sampleAvailabilities, false, teacherAvailabilityList, false);
bookingData = sampleBookings.map((item) => normalizeBooking(item));
renderAllBookings();
setActivePage("auth");
updateRoleUI();

if (teacherIdInput) {
  teacherIdInput.addEventListener("input", () => {
    syncTeacherInputs(teacherIdInput.value.trim());
    loadAvailability(teacherIdInput.value.trim());
  });
  loadAvailability(teacherIdInput.value.trim());
}
