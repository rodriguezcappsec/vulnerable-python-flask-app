// Simulating storing sensitive data in localStorage
localStorage.setItem("userToken", "example-token");
localStorage.setItem("userRole", "guest");

// Function to check role (client-side only validation)
function checkAdminAccess() {
  if (localStorage.getItem("userRole") === "admin") {
    alert("Admin access granted!");
    window.location.href = "/admin";
  } else {
    alert("You do not have admin privileges.");
  }
}
