// Add event listeners to each question item to toggle details on click
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
});
