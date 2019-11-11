import socket                   # Import socket module

port = 60001                    # Reserve a port for your service.
s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
s.bind(('', port))              # Bind to the port
s.listen(5)                     # Now wait for client connection.

while True:
    conn, addr = s.accept()     # Establish connection with client.
    print('Got connection from', addr)

    with open('received_file', 'wb') as f:
        print('file opened')
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # write data to a file
            f.write(data)

    print('Done receiving')
    conn.close()
