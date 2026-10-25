"use strict";

const searchInput = document.getElementById("searchInput");
const medicineTable = document.getElementById("medicineTable");

if (searchInput && medicineTable) {
  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();
    const rows = medicineTable.querySelectorAll("tbody tr[data-search]");
    rows.forEach((row) => {
      const searchable = row.dataset.search || "";
      row.hidden = !searchable.includes(query);
    });
  });
}

// Set the date picker minimum to today's date for new entries.
// The backend still validates the date independently.
const expiryInput = document.querySelector('input[name="expiry_date"]');
if (expiryInput) {
  const now = new Date();
  const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 10);
  expiryInput.min = localDate;
}
