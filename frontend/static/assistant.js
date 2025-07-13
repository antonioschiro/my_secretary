const appendMessage = (messageContent, side) => {
    let messages = document.getElementById('messages')
    let message = document.createElement('div')
    message.classList.add("message-type", side)
    let content = document.createTextNode(messageContent)
    message.appendChild(content)
    messages.appendChild(message)
}

let ws = new WebSocket("ws://localhost:8000/ws")

ws.onmessage = (event) => {
    appendMessage(event.data, "left")
}

const sendMessage = (event) => {
    let input = document.getElementById("messageText")
    ws.send(input.value)
    appendMessage(input.value, "right")
    input.value = ''
    event.preventDefault()
}