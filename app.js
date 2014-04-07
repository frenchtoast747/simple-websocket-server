var socket;
var port = '8002';

function start_chatting(e){
  e.preventDefault();
  var username = document.getElementById('username').value;
  var connect_form = document.getElementById('connect-form');
  var chat_app = document.getElementById('chat-app');

  connect_form.style.display = 'none';

  var status = document.getElementById('status');
  var chats = document.getElementById('chats');

  status.innerHTML = 'Connecting...';
  status.className = 'connecting';

  socket = new WebSocket('ws://localhost:'+port+'/');

  socket.onopen = function () {
    status.innerHTML = 'Connected'
    status.className = 'connected';
    chat_app.style.display = 'block';
    socket.send(username)
  };

  socket.onmessage = function (message) {
    var li = document.createElement('li');
    li.innerHTML = message.data;
    chats.appendChild(li);
  };

  function handle_input(e) {
    e.preventDefault();
    var chat_input = document.getElementById('enter-chat');
    socket.send(chat_input.value);
    chat_input.value = '';
  }

  var submit = document.getElementById('submit');
  submit.addEventListener('click', handle_input);
  var my_form = document.getElementById('my-form');
  my_form.addEventListener('submit', handle_input);
}


window.onload = function(){
  var start_chat_form = document.getElementById('start-chat-form');
  start_chat_form.addEventListener('submit', start_chatting);
};
