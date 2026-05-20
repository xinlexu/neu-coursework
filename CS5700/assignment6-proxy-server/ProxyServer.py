from socket import *
import sys

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)

#Server setup
tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.bind((sys.argv[1], 8888))
tcpSerSock.listen(1)

while 1:
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)
    
    #Receive client request
    try:
        message = tcpCliSock.recv(1024).decode()
    except:
        continue

    print(message)
    if not message:
        continue

    #Parse filename
    filename = message.split()[1].partition("/")[2]
    filetouse = "/" + filename
    
    try:
        #Check cache
        f = open(filetouse[1:], "r")
        outputdata = f.readlines()
        
        #Cache hit
        tcpCliSock.send("HTTP/1.0 200 OK\r\n".encode())
        tcpCliSock.send("Content-Type: text/html\r\n\r\n".encode())
        
        for line in outputdata:
            tcpCliSock.send(line.encode())
        print('Read from cache')
        f.close()
        
    except IOError:
        #cache miss
        c = socket(AF_INET, SOCK_STREAM)
        hostn = filename.replace("www.","",1)
        
        try:
            #connect to remote server
            c.connect((hostn, 80))
            
            #request file
            req = "GET http://" + filename + " HTTP/1.0\r\n\r\n"
            c.send(req.encode())
            
            #save to cache and send to client
            tmpFile = open("./" + filename, "wb")
            while True:
                buff = c.recv(4096)
                if len(buff) > 0:
                    tmpFile.write(buff)
                    tcpCliSock.send(buff)
                else:
                    break
            tmpFile.close()
            c.close()
            
        except:
            print("Illegal request")
        
    tcpCliSock.close()

tcpSerSock.close()