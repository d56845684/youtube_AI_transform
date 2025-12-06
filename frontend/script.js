const bookingForm = document.getElementById("booking-form");
const linkPreview = document.getElementById("link-preview");
const timeline = document.getElementById("timeline");

const sampleAvailabilities = [
  { teacher: "Chloe Chen", weekday: "Mon", window: "10:00 - 12:00" },
  { teacher: "Daniel Wu", weekday: "Wed", window: "14:00 - 16:00" },
  { teacher: "Hana Sato", weekday: "Fri", window: "09:00 - 11:00" },
];

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
  });
}

renderTimeline();
