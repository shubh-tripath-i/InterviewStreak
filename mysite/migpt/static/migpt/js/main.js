// Add event listeners to each question item to toggle details on click on interview result page
document.addEventListener('DOMContentLoaded', function () {
  const questionItems = document.querySelectorAll('.question-item');

  questionItems.forEach(item => {
    item.addEventListener('click', () => {
      const details = item.querySelector('.question-details');
      details.classList.toggle('hidden');
      const arrow = item.querySelector('.dropdown-symbol');
      arrow.classList.toggle('upward'); // Toggle the upward arrow class
    });
  });

  // Function to show setting up interview session on form submission.
  document.getElementById("interviewForm").addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the default form submission

    // Show loading message
    document.getElementById("loadingOverlay").style.display = "block";

    // Make AJAX request
    var formData = new FormData(this);
    var xhr = new XMLHttpRequest();
    xhr.open("POST", this.action);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
          var response = JSON.parse(xhr.responseText);
          if (response.status === "success") {
            // Redirect or do something upon successful submission
            window.location.href = "/start-interview/";
          } else {
            // Handle errors if needed
            alert("Error: " + response.errors);
            document.getElementById("loadingOverlay").style.display = "none";
          }
        } else {
          // Handle server errors if needed
          alert("Server error occurred. Please try again later.");
          document.getElementById("loadingOverlay").style.display = "none";
        }
      }
    };
    xhr.send(formData);
  });
  window.addEventListener("load", function () {
    document.getElementById("loadingOverlay").style.display = "none";
  });
});
