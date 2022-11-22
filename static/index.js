const prompt = document.getElementById('prompt');
const submit = document.getElementById('submit');

const websocketUrl = new URL('/api/chat', window.location.href);
if (websocketUrl.protocol === 'https'){
  websocketUrl.protocol = websocketUrl.protocol.replace('https', 'ws')
} else websocketUrl.protocol = websocketUrl.protocol.replace('http', 'ws')
let socket = new WebSocket(websocketUrl.href)

let username;

socket.onmessage = (event) => {
  const chatroom = document.getElementById('chatroom')
  const data = JSON.parse(event.data)
  switch (true){
    case 'message' in data: {
      const [sender, message] = [data.sender, data.message];
      const element = document.createElement('p');
      element.textContent = `${sender}: ${message}`;
      chatroom.append(element);  
      break;
    }
    case 'lock' in data:{
      submit.disabled = true;
      submit.textContent = "Please wait...";  
      break;
    }
    case 'unlock' in data:{
      submit.disabled = false;
      submit.textContent = "Send"  
      break;
    }
    case 'image' in data:{
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
      break;
    }
    case 'online' in data:{
      document.getElementById('onlineCount').textContent = data.online;
      break;
    }
    case 'update' in data:{
      document.getElementById('usernameDisplay').textContent = data.update;
    }
  }
}

socket.onclose = () => {
  socket = new WebSocket(websocketUrl.href)
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
