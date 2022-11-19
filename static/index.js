const prompt = document.getElementById('prompt');
const submit = document.getElementById('submit');

const websocketUrl = new URL('/api/chat', window.location.href);
if (websocketUrl.protocol === 'https'){
  websocketUrl.protocol = websocketUrl.protocol.replace('https', 'ws')
} else websocketUrl.protocol = websocketUrl.protocol.replace('http', 'ws')
const socket = new WebSocket(websocketUrl.href)

let username;

socket.onmessage = (event) => {
  const chatroom = document.getElementById('chatroom')
  const data = JSON.parse(event.data)
  if ('message' in data) {
    const [sender, message] = [data.sender, data.message];
    const element = document.createElement('p');
    element.textContent = `${sender}: ${message}`;
    chatroom.append(element);
  } else if ('lock' in data) {
    submit.disabled = true;
    submit.textContent = "Please wait...";
  } else if ('unlock' in data) {
    submit.disabled = false;
    submit.textContent = "Send"
  } else if ('image' in data) {
    const container = document.getElementById('chatContainer')
    const text = document.createElement('p')
    const image = document.createElement('img')
    const [sender, file, prompt] = [data.sender, data.image, data.prompt]
    text.textContent = `${sender}: `
    image.src = `/static/images/${file}.png`
    image.title = prompt
    text.append(image)
    chatroom.append(text)
    setTimeout(() => container.scroll({ top: container.scrollHeight, behavior: "smooth"}), 100)
  } else if ('online' in data){
    document.getElementById('onlineCount').textContent = data.online
  }
}

submit.addEventListener("click", () => {
  if (!(prompt.value.trim() === '')){
    console.log(prompt.value)
    data = {
      "sender": username,
      "message": prompt.value
    }
    socket.send(JSON.stringify(data))
  }
})

fetch('/api/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
})
.then(fetch('/api/user')
  .then(response => response.text())
  .then(text => username = text.slice(1,-1))
  .then(() => {
    document.getElementById('usernameDisplay').textContent = username;
  })
);

