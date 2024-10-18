// Vulnerable: Unsanitized use of location.hash
const searchQuery = window.location.hash.substring(1);
document.getElementById(
  "search-results"
).innerHTML = `Results for: ${searchQuery}`;
