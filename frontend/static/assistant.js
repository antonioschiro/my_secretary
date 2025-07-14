let input = document.getElementById("messageText")
let button = document.getElementById("sendButton")
let messages = document.getElementById('messages')
let ws = new WebSocket("ws://localhost:8000/ws")

const appendMessage = (messageContent, side) => {
    let message = document.createElement('div')
    message.classList.add("message-type", side)
    let content = document.createTextNode(messageContent)
    message.appendChild(content)
    messages.appendChild(message)
}

const manageToggleForm = (isDisabled) => {
    let formElements = [input, button]
    if (isDisabled){
        for (element of formElements){
                element.setAttribute("disabled", "true")
            }
    }
    else {
        for (element of formElements){
            element.removeAttribute("disabled", "false")
        }
    }
}

ws.onmessage = (event) => {
    appendMessage(event.data, "left")
    manageToggleForm(false)
}

const sendMessage = (event) => {
    ws.send(input.value)
    appendMessage(input.value, "right")
    input.value = ''
    manageToggleForm(true)
    event.preventDefault()
}