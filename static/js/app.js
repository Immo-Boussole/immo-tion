/* ── Immo-Tion Interactive UI & Navigation Helpers ──────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar drawer & Escape key listener
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.body.classList.remove("sidebar-open");
      document.querySelectorAll(".modal.active").forEach((modal) => {
        modal.classList.remove("active");
      });
    }
  });

  // Modal open/close handlers
  document.querySelectorAll("[data-modal-open]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const modalId = btn.getAttribute("data-modal-open");
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add("active");
      }
    });
  });

  document.querySelectorAll("[data-modal-close]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal");
      if (modal) {
        modal.classList.remove("active");
      }
    });
  });

  // Close modal when clicking outside content
  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("active");
      }
    });
  });

  // Property Switcher dropdown
  const propSelect = document.getElementById("propertySelector");
  if (propSelect) {
    propSelect.addEventListener("change", (e) => {
      const propId = e.target.value;
      const url = new URL(window.location.href);
      if (propId) {
        url.searchParams.set("property_id", propId);
      } else {
        url.searchParams.delete("property_id");
      }
      window.location.href = url.toString();
    });
  }
});
