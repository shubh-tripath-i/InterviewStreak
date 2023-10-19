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
