var socket;

(function(window, document, undefined){
    "use strict";
    var host = document.location.hostname;
    var port = document.location.port;

    function start_chatting(e) {
        e.preventDefault();
        var username = document.getElementById('username').value;
        var connect_form = document.getElementById('connect-form');
        var chat_app = document.getElementById('chat-app');

        connect_form.style.display = 'none';

        var status = document.getElementById('status');
        var chats = document.getElementById('chats');

        status.innerHTML = 'Connecting...';
        status.className = 'connecting';

        socket = new WebSocket('ws://' + host + ':' + port + '/');

        socket.onopen = function () {
            status.innerHTML = 'Connected';
            status.className = 'connected';
            chat_app.style.display = 'block';
            send_message({
                type: 'new_user',
                username: username
            });
        };

        socket.onmessage = function (response) {
            var tr = document.createElement('tr');
            var data = JSON.parse(response.data);
            console.log(data);
            if(data.type === 'notice') {
                data.username = '*Server Message*'
            }
            tr.innerHTML = '<td>[$1]</td><td>$2</td><td>$3</td>'
                .replace('$1', data.datetime)
                .replace('$2', data.username)
                .replace('$3', data.message);
            chats.appendChild(tr);
        };

        function handle_input(e) {
            e.preventDefault();
            var chat_input = document.getElementById('enter-chat');
            send_message({
                type: 'user_message',
                message: chat_input.value
             });
            chat_input.value = '';
        }

        var submit = document.getElementById('submit');
        submit.addEventListener('click', handle_input);
        var my_form = document.getElementById('my-form');
        my_form.addEventListener('submit', handle_input);
    }

    function send_message(data){
        socket.send(JSON.stringify(data));
    }

    window.onload = function () {
        var start_chat_form = document.getElementById('start-chat-form');
        start_chat_form.addEventListener('submit', start_chatting);
    };
})(window, document);
