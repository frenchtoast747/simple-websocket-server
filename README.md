simple-websocket-server
=======================

A simple chat server that handles simple WebSocket requests.

How to use
==========
Simply run `server.py`. This starts the server and listens on port `8002`. You can easily change the default port by editing the `PORT` global inside of `server.py`.

Next, open `index.html` in a browser. Like the server, the default port is `8002`. If you changed the default port, make sure to update the `port` variable in `app.js`.

Enter a username in the browser. If all goes well, a simple chat window should be displayed. Open `index.html` in another tab to test the chatting. If you would like to test chatting on another machine, edit the `host` global variable in `app.js` and point it to the machine on which the server is running.
