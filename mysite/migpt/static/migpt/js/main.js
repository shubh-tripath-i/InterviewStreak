document.addEventListener("DOMContentLoaded", () => {
  const chatBox = document.getElementById("chat-box");
  const messageInput = document.getElementById("message-input");
  const sendButton = document.getElementById("send-button");

  messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault(); // Prevent default Enter behavior (form submission)

          if (messageInput.value.trim() !== "") {
              sendMessage();
          }
      }
  });

  sendButton.addEventListener("click", () => {
      sendMessage();
  });

  function sendMessage() {
      const userMessage = messageInput.value.trim();

      if (userMessage) {
          appendMessage(userMessage, "outgoing");
          messageInput.value = "";

          getAIResponse(userMessage).then((aiResponse) => {
              appendMessage(aiResponse.message, "incoming");
          });
      }
  }

  function appendMessage(text, type) {
      const messageDiv = document.createElement("div");
      messageDiv.textContent = text;
      messageDiv.classList.add("message", type);
      chatBox.appendChild(messageDiv);
      chatBox.scrollTop = chatBox.scrollHeight;
  }

  async function getAIResponse(userMessage) {
      const response = await fetch("/call_llm/");
      if (response.ok) {
          return await response.json();
      } else {
          return { success: false, message: "Error getting AI response" };
      }
  }
});
