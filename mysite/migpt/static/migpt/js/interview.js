$(document).ready(function () {
    // Function to add a message to the chat box
    function addMessage(message, incoming) {
        const messageClass = incoming ? "incoming" : "outgoing";
        const messageDiv = `<div class="message ${messageClass}">${message}</div>`;
        $("#chat-box").append(messageDiv);
    }

    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");

    messageInput.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Prevents the default behavior of the Enter key (e.g., new line in a textarea)
            sendButton.click(); // Trigger a click event on the send button
        }
    });

    // Function to get the next question from Django
    function getNextQuestion() {
        $.ajax({
            url: "/get_question/",
            type: "GET",
            dataType: "json",
            success: function (data) {
                if (data.question) {
                    addMessage(data.question, true);
                    if (data.auto_answer){
                        getAutoAnswer();
                    }
                } else {
                    addMessage("No more questions.", true);
                    addMessage("You will be redirected to the result page.", true);
                    window.location.href = data.redirect;
                }
            },
            error: function (error) {
                console.error(error);
            },
        });
    }

    function getAutoAnswer() {
        $.ajax({
            url: "/get-answer-automatically/",
            type: "GET",
            dataType: "json",
            success: function (data) {
                if (data.success) {
                    const userAnswerValue = data.answer
                    $("#message-input").val(userAnswerValue);
                    $("#send-button").trigger("click"); 
                } else {
                    console.error("Failed to get answer automatically.");
                }
            },
            error: function (error) {
                console.error(error);
            },
        });
    }

    // Initialize the chat with the first question
    getNextQuestion();

    // Handle user input and submission
    $("#send-button").click(function () {
        const userAnswer = $("#message-input").val();
        if (userAnswer.trim() !== "") {
            $("#message-input").val("");
            addMessage(userAnswer, false);
            // Send the user's answer to Django for processing and update the database
            $.ajax({
                url: "/save-answer/",
                type: "POST",
                dataType: "json",
                data: {
                    answer: userAnswer,
                },
                headers: {
                    "X-CSRFToken": csrfToken,
                },
                success: function (data) {
                    if (data.success) {
                        getNextQuestion();
                    } else {
                        console.error("Failed to save answer.");
                    }
                },
                error: function (error) {
                    console.error(error);
                },
            });
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const personBox = document.getElementById('candidate-box');
    const personName = document.getElementById('candidate-name');
    const videoContainer = document.getElementById('videoContainer');
    const videoElement = document.getElementById('videoElement');

    personBox.addEventListener('mouseenter', () => {
        disableVideoButton.style.display = 'block';
        enableVideoButton.style.display = 'block';
    });

    personBox.addEventListener('mouseleave', () => {
        disableVideoButton.style.display = 'none';
        enableVideoButton.style.display = 'none';
    });

    disableVideoButton.addEventListener('click', async () => {
    const videoElement = document.getElementById('videoElement');

    if (videoElement.srcObject) {
        const tracks = videoElement.srcObject.getTracks();

        // Suspend the video element to try to stop the camera feed
        videoElement.pause();
        
        // Stop each track and wait for the promises to resolve
        await Promise.all(tracks.map(track => track.stop()));

        // Set srcObject to null after stopping the tracks
        videoElement.srcObject = null;
        videoContainer.style.display = 'none'; // Hide the video container
        personName.style.display = 'flex'; // Show the person's name
    }
});
    enableVideoButton.addEventListener('click', () => {
        handleVideoPermission();
    });

    function handleVideoPermission() {
        navigator.mediaDevices.getUserMedia({ video: true }).then(() => {
            // If permission is granted, display the video
            personName.style.display = 'none';
            videoContainer.style.display = 'block';
            navigator.mediaDevices.getUserMedia({ video: true })
                .then((stream) => {
                    videoElement.srcObject = stream;
                })
                .catch((error) => {
                    console.error('Error accessing the camera:', error);
                });
        })
        .catch(() => {
            // If permission is not granted, display the person's name
            personName.style.display = 'flex';
            videoContainer.style.display = 'none';
        });
    }

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        handleVideoPermission();
    } else {
        alert('Sorry, camera access is not supported in this browser.');
    }
});

document.getElementById('menuBtn').addEventListener('click', function() {
    var menu = document.querySelector('.interview-menu-expand');
  menu.classList.toggle('show');
    });

document.addEventListener('click', function(event) {
var menu = document.querySelector('.interview-menu-expand');
if (menu.classList.contains('show') && event.target.closest('.interview-menu') === null) {
    menu.classList.remove('show');
}
});

const messageInput = document.getElementById('message-input');
const voiceInputIcon = document.getElementById('voice-input-icon');
let recognition;

// Function to start voice recognition
function startRecognition() {
  recognition = new webkitSpeechRecognition(); // Create a new instance
  recognition.lang = 'en-US'; // Set the language
  
  recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    messageInput.value += transcript + ' '; // Append recognized text
  };
  
  recognition.onend = function() {
    recognition.stop();
    startRecognition(); // Restart recognition on end (continuous listening)
  };
  
  recognition.start(); // Start listening
}

// Toggle voice recognition on icon click
voiceInputIcon.addEventListener('click', function() {
  if (!recognition) {
    voiceInputIcon.classList.remove('fa-microphone');
    voiceInputIcon.classList.add('fa-microphone-slash');
    startRecognition();
  } else {
    voiceInputIcon.classList.remove('fa-microphone-slash');
    voiceInputIcon.classList.add('fa-microphone');
    recognition.stop();
    recognition = undefined;
  }
});
