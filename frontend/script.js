const bookingForm = document.getElementById("booking-form");
const linkPreview = document.getElementById("link-preview");
const timeline = document.getElementById("timeline");
const timelineStatus = document.getElementById("timeline-status");
const languageToggle = document.getElementById("language-toggle");
const bookingTable = document.querySelector("#booking-table tbody");
const teacherBookingTable = document.querySelector("#teacher-booking-table tbody");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const bookingStatus = document.getElementById("booking-status");
const teacherBookingStatus = document.getElementById("teacher-booking-status");
const selectedSlotView = document.getElementById("selected-slot");
const loadAvailabilityBtn = document.getElementById("load-availability");
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
const adminConsole = document.getElementById("admin-console");
const adminStatus = document.getElementById("admin-status");
const adminSearchForm = document.getElementById("admin-search-form");
const adminEmailInput = document.getElementById("admin-email");
const adminUserSummary = document.getElementById("admin-user-summary");
const adminStudentTools = document.getElementById("admin-student-tools");
const adminTeacherTools = document.getElementById("admin-teacher-tools");
const adminTeacherSelect = document.getElementById("admin-teacher-select");
const adminBookingTimeline = document.getElementById("admin-booking-timeline");
const adminBookBtn = document.getElementById("admin-book");
const adminLoadAvailabilityBtn = document.getElementById("admin-load-availability");
const adminPlatformSelect = document.getElementById("admin-platform");
const adminBookingTable = document.querySelector("#admin-booking-table tbody");
const adminAvailabilityForm = document.getElementById("admin-availability-form");
const adminAvailabilityList = document.getElementById("admin-availability-list");
const adminAvailabilityStatus = document.getElementById("admin-availability-status");
const adminAvailabilityId = document.getElementById("admin-availability-id");
const adminResetAvailabilityBtn = document.getElementById("admin-reset-availability");
const adminAvailabilityDate = document.getElementById("admin-availability-date");
const adminAvailabilityStart = document.getElementById("admin-availability-start");
const adminAvailabilityEnd = document.getElementById("admin-availability-end");

const translations = {
  zh: {
    "page-title": "學生預約入口",
    "language-toggle": "English",
    "badges-auth": "學生登入 / 註冊",
    "badges-jwt": "JWT 驗證",
    "badges-booking": "立即預約",
    "hero-title": "線上家教預約中心",
    "hero-description":
      "學生登入或註冊後，即可查看老師可預約時段，點擊選擇並送出課程預約，同時在同一頁面檢視自己的預約清單。",
    "hero-note": "若未啟動後端，畫面會顯示示範資料，方便快速瀏覽流程。",
    "steps-title": "使用步驟",
    "steps-item1": "註冊並登入取得 Token。",
    "steps-item2": "自動切換到「預約介面」。",
    "steps-item3": "點選老師時段，確認後送出預約。",
    "nav-auth": "登入 / 註冊",
    "nav-booking": "預約介面",
    "login-title": "登入",
    "login-description": "輸入帳密後即可取得 JWT Token，頁面會自動切換到預約介面。",
    "login-email": "Email",
    "login-password": "密碼",
    "role-student": "學生",
    "role-teacher": "教師",
    "login-submit": "登入並取得 Token",
    "register-title": "註冊",
    "register-description": "建立學生帳號，立即登入並查看老師空檔。",
    "register-name": "姓名",
    "register-email": "Email",
    "register-password": "密碼",
    "register-submit": "建立新帳號",
    "role-admin": "管理員",
    "admin-console-title": "管理員控制台",
    "admin-console-description": "輸入 Email 以查詢任一使用者",
    "admin-search-label": "使用者 Email",
    "admin-search-placeholder": "user@example.com",
    "admin-search-button": "查詢",
    "admin-student-title": "為學生預約",
    "admin-teacher-label": "選擇老師",
    "admin-book": "代為預約",
    "admin-teacher-title": "教師時段維護",
    "admin-availability-submit": "新增 / 更新時段",
    "admin-availability-reset": "重設",
    "admin-bookings-title": "使用者預約紀錄",
    "admin-search-success": "已載入 {email} 的資料 ({role})",
    "admin-search-failure": "查詢失敗：{message}",
    "admin-booking-success": "已為 {email} 預約完成",
    "admin-booking-error": "預約失敗：{message}",
    "admin-slot-required": "請先載入並選擇時段",
    "admin-teacher-required": "請選擇老師後再載入時段",
    "admin-availability-saved": "已更新老師時段 {date} {range}",
    "admin-availability-error": "更新失敗：{message}",
    "admin-availability-deleted": "已刪除時段",
    "booking-select-title": "選擇可預約時段",
    "booking-status-placeholder": "請選擇老師或使用示範資料",
    "booking-teacher-label": "老師",
    "booking-teacher-placeholder": "選擇老師",
    "booking-load-button": "載入時段",
    "booking-confirm-title": "預約確認",
    "booking-confirm-description": "點選左側任一時間後，會自動帶入預約表單。送出時會附帶登入 Token。",
    "booking-empty-slot": "尚未選取時段",
    "booking-platform-label": "平台",
    "booking-topic-label": "主題（選填）",
    "booking-topic-placeholder": "如：口說練習",
    "booking-submit": "送出預約",
    "booking-time-pending": "預約時間待確認",
    "booking-timeline-live": "Live API",
    "booking-timeline-sample": "示範資料",
    "booking-timeline-bookable": "可預約",
    "booking-timeline-booked": "已預約",
    "booking-timeline-select": "選擇",
    "booking-timeline-no-date": "未指定日期",
    "booking-teacher-fallback": "老師",
    "booking-no-teacher": "請先選擇老師",
    "booking-no-slots": "目前無可預約時段",
    "booking-loaded-slots": "{teacher}目前有 {count} 筆可預約時段",
    "booking-load-error": "載入失敗：{message}",
    "booking-sample-status": "未登入，顯示示範預約",
    "booking-login-required": "請先登入取得 Token 後再預約",
    "booking-select-required": "請先選擇可預約時段",
    "booking-success": "預約成功！會議連結：{link}",
    "booking-failure": "預約失敗：{message}",
    "booking-cancelled": "預約已取消",
    "booking-cancel-failure": "取消失敗：{message}",
    "cancel-default-reason": "學生取消預約",
    "teacher-tools-title": "教師時段管理",
    "teacher-tools-status": "需以教師身分登入",
    "teacher-tools-description": "教師登入後可新增可預約時段，並查看自己目前的課程預約／會議資訊。",
    "teacher-date": "日期",
    "teacher-weekday": "系統判定星期",
    "teacher-start": "開始時間",
    "teacher-end": "結束時間",
    "teacher-add": "新增可預約時段",
    "teacher-availability-title": "我的可預約時段",
    "teacher-availability-label": "尚未載入",
    "teacher-bookings-title": "教師課程 / 會議",
    "teacher-booking-status": "需以教師身分登入",
    "teacher-mode": "教師模式：{email}",
    "teacher-not-teacher": "登入角色非教師",
    "teacher-need-login": "需教師登入",
    "teacher-availability-count": "共 {count} 筆可預約時段",
    "teacher-availability-error": "教師時段載入失敗：{message}，改用示範資料",
    "bookings-title": "我的預約",
    "bookings-status": "尚未登入，顯示示範資料",
    "bookings-description": "登入後會帶入 JWT Token 呼叫 <code>/bookings</code>，只顯示當前學生的預約紀錄。",
    "table-student": "學生",
    "table-teacher": "老師",
    "table-time": "時間",
    "table-platform": "平台",
    "table-status": "狀態",
    "table-reason": "原因",
    "table-link": "連結",
    "table-recording": "錄影",
    "table-action": "操作",
    "action-cancel-booking": "取消預約",
    "action-cancelled": "已取消",
    "action-drive-link": "Drive 連結",
    "action-fetch-recording": "取得錄影",
    "action-meeting-id": "Meeting ID",
    "cancel-eyebrow": "預約取消",
    "cancel-title": "確認取消這筆預約嗎？",
    "cancel-description": "取消後將會移除行事曆邀請並釋放老師時段。",
    "cancel-reason-label": "取消原因（選填）",
    "cancel-reason-placeholder": "例如：臨時有事，想重新預約",
    "cancel-dismiss": "不用，返回",
    "cancel-confirm": "確認取消",
    "status-success": "成功",
    "status-cancelled": "取消",
    "status-pending": "待確認",
    "teacher-booking-loaded": "教師已載入 {count} 筆課程/會議",
    "booking-loaded": "已載入 {count} 筆預約",
    "booking-load-failure": "讀取預約失敗：{message}，顯示示範資料",
    "teacher-booking-failure": "教師列表載入失敗：{message}，顯示示範資料",
    "teacher-add-invalid-date": "請選擇有效的日期與時間",
    "teacher-add-different-day": "開始與結束時間需在同一天",
    "teacher-add-invalid-range": "請輸入有效的開始與結束時間",
    "teacher-add-created": "已新增 {date} ({weekday}) {range}",
    "teacher-add-unauthorized": "僅教師可以新增可預約時段",
    "teacher-add-error": "新增失敗：{message}",
    "login-success": "登入成功，已取得存取權杖",
    "login-current-user": "使用者：{email}（{role}）",
    "login-failure": "登入失敗：{message}",
    "register-success": "註冊成功：{email}（{role}），請返回登入",
    "register-failure": "註冊失敗：{message}",
    "recording-success": "錄影檔案已上傳到雲端：{detail}",
    "recording-failure": "取得錄影失敗：{message}",
    "prompt-share-email": "輸入要分享錄影檔案的 Email",
  },
  en: {
    "page-title": "Student Booking Portal",
    "language-toggle": "中文",
    "badges-auth": "Student Login / Register",
    "badges-jwt": "JWT Auth",
    "badges-booking": "Book Now",
    "hero-title": "Online Tutor Booking Center",
    "hero-description":
      "Log in or register to browse teachers' available slots, pick a time, submit a booking, and view your reservations on one page.",
    "hero-note": "If the backend is not running, sample data will appear so you can preview the flow quickly.",
    "steps-title": "How it works",
    "steps-item1": "Register and log in to get a token.",
    "steps-item2": "Switch to the booking view automatically.",
    "steps-item3": "Click a teacher's slot, confirm, and submit.",
    "nav-auth": "Login / Register",
    "nav-booking": "Booking",
    "login-title": "Login",
    "login-description": "Enter your credentials to get a JWT token. The page will switch to booking automatically.",
    "login-email": "Email",
    "login-password": "Password",
    "role-student": "Student",
    "role-teacher": "Teacher",
    "login-submit": "Login and get token",
    "register-title": "Register",
    "register-description": "Create a student account to log in right away and check open slots.",
    "register-name": "Full name",
    "register-email": "Email",
    "register-password": "Password",
    "register-submit": "Create account",
    "role-admin": "Admin",
    "admin-console-title": "Admin console",
    "admin-console-description": "Search any user by email",
    "admin-search-label": "User email",
    "admin-search-placeholder": "user@example.com",
    "admin-search-button": "Search",
    "admin-student-title": "Book for a student",
    "admin-teacher-label": "Pick teacher",
    "admin-book": "Book on behalf",
    "admin-teacher-title": "Teacher availability upkeep",
    "admin-availability-submit": "Create / update slot",
    "admin-availability-reset": "Reset",
    "admin-bookings-title": "User bookings",
    "admin-search-success": "Loaded {email} ({role})",
    "admin-search-failure": "Lookup failed: {message}",
    "admin-booking-success": "Booked successfully for {email}",
    "admin-booking-error": "Booking failed: {message}",
    "admin-slot-required": "Load and pick a slot first",
    "admin-teacher-required": "Pick a teacher before loading slots",
    "admin-availability-saved": "Updated slot {date} {range}",
    "admin-availability-error": "Update failed: {message}",
    "admin-availability-deleted": "Slot removed",
    "booking-select-title": "Pick a bookable slot",
    "booking-status-placeholder": "Select a teacher or use sample data",
    "booking-teacher-label": "Teacher",
    "booking-teacher-placeholder": "Choose a teacher",
    "booking-load-button": "Load availability",
    "booking-confirm-title": "Booking confirmation",
    "booking-confirm-description": "After clicking a time on the left, the booking form fills in automatically. Your token is sent on submit.",
    "booking-empty-slot": "No slot selected",
    "booking-platform-label": "Platform",
    "booking-topic-label": "Topic (optional)",
    "booking-topic-placeholder": "e.g. Speaking practice",
    "booking-submit": "Submit booking",
    "booking-timeline-live": "Live API",
    "booking-timeline-sample": "Sample",
    "booking-timeline-bookable": "Bookable",
    "booking-timeline-booked": "Booked",
    "booking-timeline-select": "Select",
    "booking-timeline-no-date": "No date specified",
    "booking-teacher-fallback": "Teacher",
    "booking-no-teacher": "Pick a teacher first",
    "booking-no-slots": "No bookable slots",
    "booking-loaded-slots": "{teacher} has {count} bookable slots",
    "booking-load-error": "Load failed: {message}",
    "booking-sample-status": "Showing sample bookings while logged out",
    "booking-login-required": "Please log in to book a slot",
    "booking-select-required": "Select a bookable slot first",
    "booking-success": "Booked! Meeting link: {link}",
    "booking-failure": "Booking failed: {message}",
    "booking-cancelled": "Booking cancelled",
    "booking-cancel-failure": "Cancel failed: {message}",
    "cancel-default-reason": "Student cancelled booking",
    "teacher-tools-title": "Teacher availability tools",
    "teacher-tools-status": "Teacher login required",
    "teacher-tools-description": "Teachers can add bookable slots and review their lessons or meetings after logging in.",
    "teacher-date": "Date",
    "teacher-weekday": "Detected weekday",
    "teacher-start": "Start time",
    "teacher-end": "End time",
    "teacher-add": "Add availability",
    "teacher-availability-title": "My availability",
    "teacher-availability-label": "Not loaded",
    "teacher-bookings-title": "Teacher lessons / meetings",
    "teacher-booking-status": "Teacher login required",
    "teacher-mode": "Teacher mode: {email}",
    "teacher-not-teacher": "Logged in as non-teacher",
    "teacher-need-login": "Teacher login required",
    "teacher-availability-count": "{count} available slots",
    "teacher-availability-error": "Availability failed: {message}. Using sample data",
    "bookings-title": "My bookings",
    "bookings-status": "Showing samples while logged out",
    "bookings-description": "After login, your JWT token calls <code>/bookings</code> to show only your records.",
    "table-student": "Student",
    "table-teacher": "Teacher",
    "table-time": "Time",
    "table-platform": "Platform",
    "table-status": "Status",
    "table-reason": "Reason",
    "table-link": "Link",
    "table-recording": "Recording",
    "table-action": "Actions",
    "action-cancel-booking": "Cancel booking",
    "action-cancelled": "Cancelled",
    "action-drive-link": "Drive link",
    "action-fetch-recording": "Get recording",
    "action-meeting-id": "Meeting ID",
    "cancel-eyebrow": "Cancel booking",
    "cancel-title": "Cancel this booking?",
    "cancel-description": "This removes the calendar invite and frees the teacher's time.",
    "cancel-reason-label": "Reason (optional)",
    "cancel-reason-placeholder": "Example: Something came up, I need to reschedule",
    "cancel-dismiss": "No, go back",
    "cancel-confirm": "Confirm cancel",
    "status-success": "Succeeded",
    "status-cancelled": "Cancelled",
    "status-pending": "Pending",
    "teacher-booking-loaded": "Teacher loaded {count} bookings/meetings",
    "booking-loaded": "Loaded {count} bookings",
    "booking-load-failure": "Bookings failed: {message}. Showing samples",
    "teacher-booking-failure": "Teacher bookings failed: {message}. Showing samples",
    "teacher-add-invalid-date": "Choose a valid date and time",
    "teacher-add-different-day": "Start and end must be on the same day",
    "teacher-add-invalid-range": "Enter a valid start and end time",
    "teacher-add-created": "Added {date} ({weekday}) {range}",
    "teacher-add-unauthorized": "Only teachers can add availability",
    "teacher-add-error": "Create failed: {message}",
    "login-success": "Logged in. Token ready",
    "login-current-user": "User: {email} ({role})",
    "login-failure": "Login failed: {message}",
    "register-success": "Registered: {email} ({role}). Please log in",
    "register-failure": "Register failed: {message}",
    "recording-success": "Recording uploaded: {detail}",
    "recording-failure": "Get recording failed: {message}",
    "prompt-share-email": "Enter an email to share the recording",
  },
};

let currentLocale = "zh";
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
let currentTimelineData = sampleAvailabilities;
let currentTimelineFromApi = false;
let currentTeacherTimelineData = sampleAvailabilities;
let currentTeacherTimelineFromApi = false;
let adminTargetUser = null;
let adminTargetBookings = [];
let adminTargetAvailabilities = [];
let adminSelectedSlot = null;
let adminTimelineSlots = [];

function t(key, vars = {}) {
  const template = translations[currentLocale]?.[key] ?? translations.zh?.[key] ?? vars?.fallback ?? key;
  return template.replace(/\{(\w+)\}/g, (match, name) => (vars[name] !== undefined ? vars[name] : match));
}

function applyTranslations() {
  document.documentElement.lang = currentLocale === "en" ? "en" : "zh-Hant";
  document.title = t("page-title");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    const value = t(key);
    if (el.dataset.i18nHtml === "true") {
      el.innerHTML = value;
    } else {
      el.textContent = value;
    }
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    el.placeholder = t(key);
  });
  if (languageToggle) {
    languageToggle.textContent = currentLocale === "en" ? "中文" : "English";
  }
  renderTimeline(currentTimelineData, currentTimelineFromApi, timeline, true);
  renderTimeline(currentTeacherTimelineData, currentTeacherTimelineFromApi, teacherAvailabilityList, false);
  renderAllBookings();
  if (selectedSlot) {
    selectSlot(selectedSlot);
  } else if (selectedSlotView) {
    selectedSlotView.textContent = t("booking-empty-slot");
  }
  syncTranslatedStatuses();
}

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
  if (!slot) return t("booking-time-pending");
  const dateLabel = slot.availability_date
    ? `${formatDateValue(slot.availability_date)} (${slot.weekday || ""})`
    : slot.weekday || t("booking-timeline-no-date");
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

function openCancelModal(bookingId, defaultReason = t("cancel-default-reason")) {
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

    const reason = cancelReasonInput?.value?.trim() || t("cancel-default-reason");
    try {
      await apiFetch(`/bookings/${pendingCancelBookingId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status_desc: reason }),
      });
      setStatus(bookingStatus, t("booking-cancelled"));
      await refreshBookings();
    } catch (error) {
      setStatus(bookingStatus, t("booking-cancel-failure", { message: error.message }), true);
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
  const studentEmail = item.student?.email || item.student_email || item.studentEmail || "";
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
      t("booking-time-pending");

    return {
      id: item.id,
      student_id: item.student_id,
      teacher_id: item.teacher_id,
      student: studentName,
      teacher: teacherName,
      platform: item.platform || "Zoom",
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
      student_email: studentEmail,
    };
  }

  return {
    id: item.id,
    student_id: item.student_id,
    teacher_id: item.teacher_id,
    student: studentName,
    teacher: teacherName,
    platform: item.platform || "Zoom",
    time: item.time ?? describeAvailability(item.availability),
    status: item.status ?? "成功",
    status_desc: item.status_desc || "",
    link: item.link ?? item.conference_link ?? buildConferenceLink(item.teacher, item.student, item.platform),
    meeting_id: meetingId,
    drive_link: driveLink,
    zoom_recording: zoomRecording,
    student_email: studentEmail,
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
  const visibleList = selectable ? activeList.filter((slot) => !slot.is_booked) : activeList;

  if (target === timeline) {
    currentTimelineData = list;
    currentTimelineFromApi = fromApi;
  }
  if (target === teacherAvailabilityList) {
    currentTeacherTimelineData = list;
    currentTeacherTimelineFromApi = fromApi;
  }

  target.innerHTML = visibleList
    .map((slot) => {
      const dateLabel = slot.availability_date
        ? `${formatDateValue(slot.availability_date)} (${slot.weekday || ""})`
        : slot.weekday || t("booking-timeline-no-date");
      const teacherName = slot.teacher?.full_name || slot.teacher_full_name || slot.teacher || t("booking-teacher-fallback");
      const isBooked = Boolean(slot.is_booked);
      return `
        <div class="timeline-step" data-slot-id="${slot.id || ""}">
          <div class="timeline-meta">
            <strong>${teacherName}</strong> • ${dateLabel} • ${formatTimeRange(slot)}
            <div class="tag-row">
              <span class="tag">${fromApi ? t("booking-timeline-live") : t("booking-timeline-sample")}</span>
              <span class="tag ${isBooked ? "tag-muted" : ""}">${isBooked ? t("booking-timeline-booked") : t("booking-timeline-bookable")}</span>
            </div>
          </div>
          ${
            selectable
              ? `<button class="ghost ${isBooked ? "booked" : ""}" data-action="select-slot" ${isBooked ? "disabled" : ""}>${t(
                  "booking-timeline-select",
                )}</button>`
              : ""
          }
        </div>
      `;
    })
    .join("");

  if (!selectable) return;
  target.querySelectorAll("[data-action=select-slot]").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      const wrapper = event.target.closest(".timeline-step");
      const id = wrapper?.dataset.slotId;
      const slot = visibleList.find((item) => `${item.id}` === id);
      selectSlot(slot || visibleList[0]);
    });
  });
}

function localizeStatusLabel(status) {
  if (!status) return "";
  const normalized = status.toString().toLowerCase();
  if (normalized.includes("取消") || normalized.includes("cancel")) return t("status-cancelled", { fallback: status });
  if (normalized.includes("成功") || normalized.includes("succeed") || normalized.includes("confirm"))
    return t("status-success", { fallback: status });
  if (normalized.includes("待") || normalized.includes("pending") || normalized.includes("await"))
    return t("status-pending", { fallback: status });
  return status;
}

function updateTimelineStatusMessage() {
  if (!timelineStatus) return;
  const activeList = Array.isArray(currentTimelineData) ? currentTimelineData.filter((slot) => !slot.deleted_at) : [];
  const bookableSlots = activeList.filter((slot) => !slot.is_booked);
  if (!bookableSlots.length) {
    const messageKey = currentTimelineData?.length ? "booking-no-slots" : "booking-status-placeholder";
    setStatus(timelineStatus, t(messageKey), messageKey !== "booking-status-placeholder");
    return;
  }
  const teacherName = bookableSlots[0]?.teacher?.full_name;
  const label = teacherName ? `${teacherName}` : t("booking-teacher-fallback");
  setStatus(timelineStatus, t("booking-loaded-slots", { teacher: label, count: bookableSlots.length }));
}

function syncTranslatedStatuses() {
  updateTimelineStatusMessage();
  if (bookingStatus) {
    if (!authToken) {
      setStatus(bookingStatus, t("booking-sample-status"));
    } else {
      const studentViewLength =
        currentUser?.role === "student" ? filterStudentBookings(bookingData).length : bookingData.length;
      setStatus(bookingStatus, t("booking-loaded", { count: studentViewLength }));
    }
  }
  if (teacherBookingStatus) {
    if (!teacherBookingStatus.classList.contains("error")) {
      if (currentUser?.role === "teacher") {
        setStatus(teacherBookingStatus, t("teacher-booking-loaded", { count: bookingData.length }));
      } else {
        setStatus(teacherBookingStatus, t("teacher-tools-status"), true);
      }
    }
  }
  if (teacherAvailabilityLabel) {
    if (!teacherAvailabilityLabel.classList.contains("error")) {
      if (!authToken || currentUser?.role !== "teacher") {
        setStatus(teacherAvailabilityLabel, currentUser ? t("teacher-not-teacher") : t("teacher-need-login"), true);
      } else {
        setStatus(teacherAvailabilityLabel, t("teacher-availability-count", { count: currentTeacherTimelineData?.length || 0 }));
      }
    }
  }
  if (teacherToolsStatus) {
    setStatus(
      teacherToolsStatus,
      currentUser?.role === "teacher" ? t("teacher-mode", { email: currentUser?.email }) : t("teacher-tools-status"),
      currentUser?.role !== "teacher" && !!currentUser,
    );
  }
}

function renderBookings(targetTable, data) {
  if (!targetTable) return;
  const normalized = data.map(normalizeBooking).filter(Boolean);
  const isStudentTable = targetTable === bookingTable;
  targetTable.innerHTML = normalized
    .map((item) => {
      const isCancelled = (item.status || "").toString().toLowerCase().includes("取消") ||
        (item.status || "").toString().toLowerCase().includes("cancel");
      const canCancel =
        isStudentTable &&
        currentUser?.role === "student" &&
        `${item.student_id}` === `${currentUser?.id}` &&
        !isCancelled;
      const statusLabel = localizeStatusLabel(item.status || "成功");
      const statusBadge = `<span class="tag ${isCancelled ? "tag-muted" : ""}">${statusLabel}</span>`;
      const statusDesc = item.status_desc || "";
      const defaultReason = statusDesc || t("cancel-default-reason");
      const actionCell = isStudentTable
        ? item.drive_link
          ? `<a class="muted" href="${escapeAttribute(item.drive_link)}" target="_blank" rel="noopener">${t("action-drive-link")}</a>`
          : `<button class="ghost" data-action="cancel-booking" data-booking-id="${item.id}" data-default-reason="${escapeAttribute(defaultReason)}" ${canCancel ? "" : "disabled"}>${isCancelled ? t("action-cancelled") : t("action-cancel-booking")}</button>`
        : "";
      const recordingCell = !isStudentTable
        ? `<div class="stacked">
            ${
              item.platform === "Zoom"
                ? item.drive_link
                  ? `<a class="muted" href="${escapeAttribute(item.drive_link)}" target="_blank" rel="noopener">${t("action-drive-link")}</a>`
                  : `<button class="ghost" data-action="fetch-recording" data-booking-id="${item.id}" data-meeting-id="${escapeAttribute(item.meeting_id || "")}" data-student-email="${escapeAttribute(item.student_email || "")}">${t("action-fetch-recording")}</button>`
                : "-"
            }
            ${item.meeting_id ? `<span class="muted">${t("action-meeting-id")}: ${escapeAttribute(item.meeting_id)}</span>` : ""}
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
        const defaultReason = event.currentTarget.dataset.defaultReason || t("cancel-default-reason");
        openCancelModal(bookingId, defaultReason);
      });
    });
  } else {
    targetTable.querySelectorAll("[data-action=fetch-recording]").forEach((btn) => {
      btn.addEventListener("click", async (event) => {
        const bookingId = event.currentTarget.dataset.bookingId;
        const meetingId = event.currentTarget.dataset.meetingId;
        const defaultEmail =
          event.currentTarget.dataset.studentEmail || currentUser?.email || "";
        const shareEmail = prompt(t("prompt-share-email"), defaultEmail);
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
            t("recording-success", { detail: record.drive_share_link || record.drive_file_id || "完成" }),
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
          setStatus(teacherBookingStatus, t("recording-failure", { message: error.message }), true);
        }
      });
    });
  }
}

function renderAllBookings() {
  const studentView = currentUser?.role === "student" ? filterStudentBookings(bookingData) : bookingData;
  renderBookings(bookingTable, studentView);
  renderBookings(teacherBookingTable, bookingData);
  renderBookings(adminBookingTable, adminTargetBookings);
}

function renderAdminBookingTimeline(list = [], fromApi = false) {
  if (!adminBookingTimeline) return;
  const activeList = Array.isArray(list) ? list.filter((slot) => !slot.deleted_at) : [];
  const bookable = activeList.filter((slot) => !slot.is_booked);
  adminTimelineSlots = bookable;
  if (!bookable.length) {
    adminBookingTimeline.innerHTML = `<p class="muted">${fromApi ? t("booking-no-slots") : ""}</p>`;
    return;
  }

  adminBookingTimeline.innerHTML = bookable
    .map((slot) => {
      const label = describeAvailability(slot);
      const teacherName = slot.teacher?.full_name || slot.teacher_full_name || slot.teacher || t("booking-teacher-fallback");
      return `
        <div class="timeline-step" data-slot-id="${slot.id}">
          <div class="timeline-meta">
            <strong>${escapeAttribute(teacherName)}</strong> • ${label}
          </div>
          <button class="ghost" data-action="admin-select-slot">${t("booking-timeline-select")}</button>
        </div>
      `;
    })
    .join("");

  adminBookingTimeline.querySelectorAll("[data-action=admin-select-slot]").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      const wrapper = event.currentTarget.closest(".timeline-step");
      const slotId = wrapper?.dataset.slotId;
      adminSelectedSlot = bookable.find((slot) => `${slot.id}` === `${slotId}`) || null;
      if (adminSelectedSlot && adminStatus) {
        setStatus(adminStatus, describeAvailability(adminSelectedSlot));
      }
    });
  });
}

function renderAdminAvailabilities(list = []) {
  if (!adminAvailabilityList) return;
  if (!list.length) {
    adminAvailabilityList.innerHTML = `<p class="muted">${t("teacher-availability-label")}</p>`;
    return;
  }
  adminAvailabilityList.innerHTML = list
    .map((slot) => {
      const label = describeAvailability(slot);
      return `
        <div class="timeline-step" data-slot-id="${slot.id}">
          <div class="timeline-meta">${escapeAttribute(label)}</div>
          <div class="tag-row">
            <button class="ghost" data-action="admin-edit-slot" data-slot-id="${slot.id}">Edit</button>
            <button class="ghost" data-action="admin-delete-slot" data-slot-id="${slot.id}">Delete</button>
          </div>
        </div>
      `;
    })
    .join("");

  adminAvailabilityList.querySelectorAll("[data-action=admin-edit-slot]").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      const slotId = event.currentTarget.dataset.slotId;
      const slot = list.find((item) => `${item.id}` === `${slotId}`);
      if (!slot) return;
      if (adminAvailabilityId) adminAvailabilityId.value = slot.id;
      if (adminAvailabilityDate) adminAvailabilityDate.value = slot.availability_date || "";
      const startValue = (slot.start_time || "").toString().slice(0, 5);
      const endValue = (slot.end_time || "").toString().slice(0, 5);
      if (adminAvailabilityStart) adminAvailabilityStart.value = startValue;
      if (adminAvailabilityEnd) adminAvailabilityEnd.value = endValue;
      setStatus(adminAvailabilityStatus, describeAvailability(slot));
    });
  });

  adminAvailabilityList.querySelectorAll("[data-action=admin-delete-slot]").forEach((btn) => {
    btn.addEventListener("click", async (event) => {
      const slotId = event.currentTarget.dataset.slotId;
      if (!slotId) return;
      try {
        await apiFetch(`/availability/${slotId}`, { method: "DELETE" });
        setStatus(adminAvailabilityStatus, t("admin-availability-deleted"));
        if (adminTargetUser?.email) {
          await loadAdminUser(adminTargetUser.email);
        }
      } catch (error) {
        setStatus(adminAvailabilityStatus, t("admin-availability-error", { message: error.message }), true);
      }
    });
  });
}

async function loadAdminUser(email) {
  if (!email) return;
  try {
    const data = await apiFetch(`/admin/users/lookup?email=${encodeURIComponent(email)}`);
    adminTargetUser = data.user;
    adminTargetBookings = data.bookings || [];
    adminTargetAvailabilities = data.availabilities || [];
    adminSelectedSlot = null;
    renderAdminBookingTimeline([]);
    renderAdminUserData();
    setStatus(adminStatus, t("admin-search-success", { email: adminTargetUser.email, role: adminTargetUser.role }));
  } catch (error) {
    adminTargetUser = null;
    adminTargetBookings = [];
    adminTargetAvailabilities = [];
    renderAdminUserData();
    setStatus(adminStatus, t("admin-search-failure", { message: error.message }), true);
  }
}

function renderAdminUserData() {
  if (!adminUserSummary) return;
  const hasUser = Boolean(adminTargetUser);
  adminUserSummary.textContent = hasUser
    ? `${adminTargetUser.full_name} · ${adminTargetUser.email} · ${adminTargetUser.role}`
    : "";

  if (adminStudentTools) {
    adminStudentTools.hidden = !hasUser || adminTargetUser.role !== "student";
  }
  if (adminTeacherTools) {
    adminTeacherTools.hidden = !hasUser || adminTargetUser.role !== "teacher";
  }

  if (!hasUser) {
    renderBookings(adminBookingTable, []);
    renderAdminAvailabilities([]);
    renderAdminBookingTimeline([]);
    return;
  }

  renderBookings(adminBookingTable, adminTargetBookings || []);
  if (adminTargetUser.role === "teacher") {
    renderAdminAvailabilities(adminTargetAvailabilities || []);
  } else {
    renderAdminAvailabilities([]);
  }
}

async function loadAdminTeacherAvailability() {
  const teacherId = adminTeacherSelect?.value?.trim();
  if (!teacherId) {
    setStatus(adminStatus, t("admin-teacher-required"), true);
    return;
  }
  try {
    const availability = await apiFetch(`/teachers/${teacherId}/availability`);
    renderAdminBookingTimeline(availability, true);
    if (availability?.length) {
      setStatus(adminStatus, t("booking-loaded-slots", { teacher: teacherId, count: availability.length }));
    }
  } catch (error) {
    renderAdminBookingTimeline([]);
    setStatus(adminStatus, t("booking-load-error", { message: error.message }), true);
  }
}

function resetAdminAvailabilityForm() {
  if (adminAvailabilityId) adminAvailabilityId.value = "";
  adminAvailabilityForm?.reset();
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
    setStatus(bookingStatus, t("booking-sample-status"));
    setStatus(teacherBookingStatus, t("teacher-tools-status"), true);
    return;
  }

  try {
    const bookings = await apiFetch("/bookings");
    bookingData = bookings;
    renderAllBookings();
    const studentViewLength =
      currentUser?.role === "student" ? filterStudentBookings(bookings).length : bookings.length;
    setStatus(bookingStatus, t("booking-loaded", { count: studentViewLength }));
    if (teacherBookingStatus) {
      setStatus(teacherBookingStatus, t("teacher-booking-loaded", { count: bookings.length }));
    }
  } catch (error) {
    setStatus(bookingStatus, t("booking-load-failure", { message: error.message }), true);
    bookingData = sampleBookings;
    renderAllBookings();
    if (teacherBookingStatus) {
      setStatus(teacherBookingStatus, t("teacher-booking-failure", { message: error.message }), true);
    }
  }
}

async function loadAvailability(teacherId) {
  const trimmedId = teacherId?.toString().trim();
  if (!trimmedId) {
    renderTimeline([], false);
    setStatus(timelineStatus, t("booking-no-teacher"), true);
    return;
  }

  try {
    const availability = await apiFetch(`/teachers/${trimmedId}/availability`);
    const activeList = Array.isArray(availability)
      ? availability.filter((slot) => !slot.deleted_at)
      : [];
    const bookableSlots = activeList.filter((slot) => !slot.is_booked);

    if (!bookableSlots.length) {
      renderTimeline([], true);
      setStatus(timelineStatus, t("booking-no-slots"), true);
      return;
    }
    renderTimeline(bookableSlots, true);
    const teacherName = bookableSlots[0]?.teacher?.full_name;
    const label = teacherName ? `${teacherName}` : t("booking-teacher-fallback");
    setStatus(timelineStatus, t("booking-loaded-slots", { teacher: label, count: bookableSlots.length }));
  } catch (error) {
    renderTimeline([], false);
    setStatus(timelineStatus, t("booking-load-error", { message: error.message }), true);
  }
}

function renderTeacherOptions(list) {
  if (!teacherNameInput) return;
  const selected = teacherNameInput.value;
  teacherNameInput.innerHTML =
    `<option value="">${t("booking-teacher-placeholder")}</option>` +
    list.map((teacher) => `<option value="${teacher.id}">${teacher.full_name}</option>`).join("");
  if (selected) {
    teacherNameInput.value = selected;
  }
  if (adminTeacherSelect) {
    const adminSelected = adminTeacherSelect.value;
    adminTeacherSelect.innerHTML =
      `<option value="">${t("booking-teacher-placeholder")}</option>` +
      list.map((teacher) => `<option value="${teacher.id}">${teacher.full_name}</option>`).join("");
    if (adminSelected) {
      adminTeacherSelect.value = adminSelected;
    }
  }
}

async function refreshTeacherDirectory(query = "") {
  try {
    const url = query ? `/teachers?search=${encodeURIComponent(query)}` : "/teachers";
    const teachers = await apiFetch(url);
    teacherDirectory = teachers;
    renderTeacherOptions(teachers);
  } catch (error) {
    setStatus(timelineStatus, t("booking-load-error", { message: error.message }), true);
  }
}

async function refreshTeacherAvailability() {
  if (!teacherAvailabilityList) return;
  if (!authToken || !currentUser || currentUser.role !== "teacher") {
    renderTimeline(sampleAvailabilities, false, teacherAvailabilityList, false);
    setStatus(
      teacherAvailabilityLabel,
      currentUser ? t("teacher-not-teacher") : t("teacher-need-login"),
      true,
    );
    return;
  }

  try {
    const availability = await apiFetch(`/teachers/${currentUser.id}/availability`);
    renderTimeline(availability, true, teacherAvailabilityList, false);
    setStatus(teacherAvailabilityLabel, t("teacher-availability-count", { count: availability.length }));
  } catch (error) {
    renderTimeline(sampleAvailabilities, false, teacherAvailabilityList, false);
    setStatus(
      teacherAvailabilityLabel,
      t("teacher-availability-error", { message: error.message }),
      true,
    );
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

function isAdminUser() {
  return currentUser?.role === "admin" || currentUser?.role === "superuser";
}

function updateRoleUI() {
  const isTeacher = currentUser?.role === "teacher";
  const adminMode = isAdminUser();
  if (studentOnlySections.length) {
    studentOnlySections.forEach((section) => section.classList.toggle("hidden", isTeacher && !adminMode));
  }
  if (teacherTools) {
    teacherTools.classList.toggle("hidden", !isTeacher);
  }
  if (teacherToolsStatus) {
    setStatus(
      teacherToolsStatus,
      isTeacher ? t("teacher-mode", { email: currentUser?.email }) : t("teacher-tools-status"),
      !isTeacher && !!currentUser,
    );
  }
  if (adminConsole) {
    adminConsole.classList.toggle("hidden", !adminMode);
  }
  if (!isTeacher) {
    renderTimeline(sampleAvailabilities, false, teacherAvailabilityList, false);
    setStatus(teacherAvailabilityLabel, currentUser ? t("teacher-not-teacher") : t("teacher-need-login"), true);
    setStatus(teacherBookingStatus, currentUser ? t("teacher-not-teacher") : t("teacher-tools-status"), true);
    renderBookings(teacherBookingTable, bookingData);
    return;
  }

  syncTeacherInputs(currentUser?.id ? `${currentUser.id}` : teacherNameInput?.value || "");
  refreshTeacherAvailability();
}

function selectSlot(slot) {
  if (!slot) return;
  selectedSlot = slot;
  if (selectedSlotView) {
    const dateLabel = slot.availability_date
      ? `${formatDateValue(slot.availability_date)} (${slot.weekday || ""})`
      : slot.weekday;
    const teacherLabel = slot.teacher?.full_name || slot.teacher_full_name || slot.teacher || t("booking-teacher-fallback");
    selectedSlotView.textContent = `${teacherLabel} ｜ ${dateLabel} ${formatTimeRange(slot)}`;
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
  if (!teacherNameInput) return;
  if (!value) {
    teacherNameInput.value = "";
    return;
  }
  const matched = teacherDirectory.find((teacher) => `${teacher.id}` === `${value}`);
  if (matched && `${teacherNameInput.value}` !== `${matched.id}`) {
    teacherNameInput.value = `${matched.id}`;
  }
}

document.querySelectorAll("[data-nav]").forEach((tab) => {
  tab.addEventListener("click", () => {
    setActivePage(tab.dataset.nav);
    updateRoleUI();
    if (tab.dataset.nav === "booking") {
      const teacherId = teacherNameInput?.value || "";
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
    syncTeacherInputs(`${selectedId}`);
    loadAvailability(selectedId);
  });
}

if (bookingForm) {
  bookingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(bookingForm);
    const availabilityId = Number(formData.get("availabilityId"));
    const platform = formData.get("platform");

    if (!authToken) {
      setStatus(linkPreview, t("booking-login-required"), true);
      return;
    }
    if (!availabilityId) {
      setStatus(linkPreview, t("booking-select-required"), true);
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
      setStatus(linkPreview, t("booking-success", { link: normalized.link }));
      linkPreview.classList.add("status-pill");
    } catch (error) {
      setStatus(linkPreview, t("booking-failure", { message: error.message }), true);
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
      setStatus(document.getElementById("login-status"), t("login-success"));

      currentUser = await apiFetch("/users/me");
      setStatus(
        document.getElementById("login-status"),
        t("login-current-user", { email: currentUser.email, role: currentUser.role }),
      );
      updateRoleUI();
      syncTeacherInputs(currentUser?.id ? `${currentUser.id}` : teacherNameInput?.value || "");
      setActivePage("booking");
      const teacherId = teacherNameInput?.value || "";
      loadAvailability(teacherId.trim());
      await refreshBookings();
      await refreshTeacherAvailability();
    } catch (error) {
      setStatus(document.getElementById("login-status"), t("login-failure", { message: error.message }), true);
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
        t("register-success", { email: result.email, role: result.role }),
      );
    } catch (error) {
      setStatus(document.getElementById("register-status"), t("register-failure", { message: error.message }), true);
    }
  });
}

if (teacherAvailabilityForm) {
  teacherAvailabilityForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!currentUser || currentUser.role !== "teacher") {
      setStatus(teacherAvailabilityStatus, t("teacher-add-unauthorized"), true);
      return;
    }
    const formData = new FormData(teacherAvailabilityForm);
    const availabilityDate = formData.get("availabilityDate");
    const startValue = formData.get("startTime");
    const endValue = formData.get("endTime");
    const startDate = startValue && availabilityDate ? new Date(`${availabilityDate}T${startValue}`) : null;
    const endDate = endValue && availabilityDate ? new Date(`${availabilityDate}T${endValue}`) : null;

    if (!availabilityDate || !startDate || !endDate || Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      setStatus(teacherAvailabilityStatus, t("teacher-add-invalid-date"), true);
      return;
    }
    if (startDate.toDateString() !== endDate.toDateString()) {
      setStatus(teacherAvailabilityStatus, t("teacher-add-different-day"), true);
      return;
    }
    if (startDate >= endDate) {
      setStatus(teacherAvailabilityStatus, t("teacher-add-invalid-range"), true);
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
        t("teacher-add-created", {
          date: formatDateValue(created.availability_date),
          weekday: created.weekday,
          range: formatTimeRange(created),
        }),
      );
      teacherAvailabilityForm.reset();
      if (teacherDateInput) {
        teacherDateInput.value = availabilityDate;
        teacherWeekdayInput.value = deriveWeekdayLabel(availabilityDate);
      }
      syncTeacherInputs(currentUser.id ? `${currentUser.id}` : "");
      await refreshTeacherAvailability();
      if (teacherNameInput?.value) {
        loadAvailability(teacherNameInput.value.trim());
      }
    } catch (error) {
      setStatus(teacherAvailabilityStatus, t("teacher-add-error", { message: error.message }), true);
    }
  });
}

if (adminSearchForm) {
  adminSearchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!isAdminUser()) {
      setStatus(adminStatus, t("admin-search-failure", { message: "Unauthorized" }), true);
      return;
    }
    const email = adminEmailInput?.value?.trim();
    await loadAdminUser(email);
  });
}

if (adminLoadAvailabilityBtn) {
  adminLoadAvailabilityBtn.addEventListener("click", () => {
    if (!isAdminUser()) return;
    loadAdminTeacherAvailability();
  });
}

if (adminBookBtn) {
  adminBookBtn.addEventListener("click", async () => {
    if (!isAdminUser() || !adminTargetUser || adminTargetUser.role !== "student") return;
    if (!adminSelectedSlot) {
      setStatus(adminStatus, t("admin-slot-required"), true);
      return;
    }
    const platform = adminPlatformSelect?.value || "Google Meet";
    try {
      await apiFetch("/bookings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          availability_id: adminSelectedSlot.id,
          platform,
          student_id: adminTargetUser.id,
        }),
      });
      setStatus(adminStatus, t("admin-booking-success", { email: adminTargetUser.email }));
      if (adminTargetUser?.email) {
        await loadAdminUser(adminTargetUser.email);
      }
      adminSelectedSlot = null;
      renderAdminBookingTimeline([]);
    } catch (error) {
      setStatus(adminStatus, t("admin-booking-error", { message: error.message }), true);
    }
  });
}

if (adminAvailabilityForm) {
  adminAvailabilityForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!isAdminUser() || !adminTargetUser || adminTargetUser.role !== "teacher") {
      setStatus(adminAvailabilityStatus, t("admin-availability-error", { message: "Unauthorized" }), true);
      return;
    }

    const formData = new FormData(adminAvailabilityForm);
    const availabilityDate = formData.get("availabilityDate");
    const startTime = formData.get("startTime");
    const endTime = formData.get("endTime");
    const availabilityId = formData.get("availabilityId");
    const payload = {
      availability_date: availabilityDate,
      start_time: startTime,
      end_time: endTime,
    };

    try {
      if (availabilityId) {
        await apiFetch(`/availability/${availabilityId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } else {
        await apiFetch("/teachers/availability", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...payload, teacher_id: adminTargetUser.id }),
        });
      }
      setStatus(
        adminAvailabilityStatus,
        t("admin-availability-saved", {
          date: formatDateValue(availabilityDate),
          range: `${startTime} - ${endTime}`,
        }),
      );
      resetAdminAvailabilityForm();
      if (adminTargetUser?.email) {
        await loadAdminUser(adminTargetUser.email);
      }
    } catch (error) {
      setStatus(adminAvailabilityStatus, t("admin-availability-error", { message: error.message }), true);
    }
  });
}

if (adminResetAvailabilityBtn) {
  adminResetAvailabilityBtn.addEventListener("click", resetAdminAvailabilityForm);
}

if (loadAvailabilityBtn) {
  loadAvailabilityBtn.addEventListener("click", () => {
    const teacherId = teacherNameInput?.value || "";
    syncTeacherInputs(teacherId.toString().trim());
    loadAvailability(teacherId.toString().trim());
  });
}

if (languageToggle) {
  languageToggle.addEventListener("click", () => {
    currentLocale = currentLocale === "zh" ? "en" : "zh";
    applyTranslations();
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
applyTranslations();
