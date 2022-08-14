import socket
import signal
import sys
import random
import time

#mrg225 ft114

# Read a command line argument for the port where the server
# must run.
port = 8080
host_name = socket.gethostname()
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)

### Contents of pages we will serve.
# Login form
login_form = f"""
   <form action = "http://{host_name}:{port}" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
"""
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = f"""
   <h1>Welcome!</h1>
   <form action="http://{host_name}:{port}" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
"""
#makes a new cookie header, returns two values
#you can call it like this:
# number, header = make_new_cookie_header()
def make_new_cookie_header():
    rand_val = random.getrandbits(64)
    return rand_val, 'Set-Cookie: token=' + str(rand_val) + '\r\n'
#retrieves the cookie value from a request
#you can give it the entire header and it should return the cookie
#if there is no cookie it will return None
def get_cookie_from_request(request):
    for line in request.split('\n'):
        # print(line.lower())
        # print("cookie" in line.lower())
        if "cookie" in line.lower():
            split = line.split('=')
            try:
                return int(split[-1])
            except ValueError:
                return None

#### Helper functions
# Printing.
def print_value(tag, value):
    print( "Here is the", tag)
    print( "\"\"\"")
    print( value)
    print( "\"\"\"")
    print()

# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)

def main():
    passwords = {}
    secrets = {}
    cookies = {}
    for line in open("passwords.txt", "r"):
        split_line = line.split()
        passwords[split_line[0]] = split_line[1]
    for line in open("secrets.txt", "r"):
        split_line = line.split()
        secrets[split_line[0]] = split_line[1]
    

    while True:
        time.sleep(.3)
        client, addr = sock.accept()
        req = client.recv(1024).decode()
        
        header_body = req.split('\r\n\r\n')
        headers = header_body[0]
        body = '' if len(header_body) == 1 else header_body[1]
        print_value('headers', headers)
        print_value('entity body', body)
        
        received={}
        if body!='':
            received=dict([tuple(s.split("=")) for s in body.split("&")])
            
        temp="\n".join(headers.split("\r\n")[1:])
        header=dict([tuple(i.split(": ")) for i in temp.split("\n")])

        headers_to_send=""
        if "action" in received.keys() and received["action"]=="logout":
            html_content_to_send = logout_page
        elif "username" in received.keys() and "password" in received.keys():
            if received["username"] in passwords.keys() and passwords[received["username"]] == received["password"]:
                html_content_to_send = success_page + secrets[received["username"]]
                cookie = random.getrandbits(64)
                headers_to_send = "Set-Cookie: token=" + str(cookie) + "\r\n"
                if cookie not in cookies.keys():
                    cookies.update({"token=" + str(cookie):secrets[received["username"]]})
            elif "Cookie" in header.keys():
                if header["Cookie"] in cookies.keys():
                    html_content_to_send = success_page + cookies[header["Cookie"]]
                else:
                    html_content_to_send=bad_creds_page
            elif received["username"]=="" and received["password"]=="":
                html_content_to_send = login_page
            else:
                html_content_to_send = bad_creds_page
        elif "Cookie" in header.keys():
            if header["Cookie"] in cookies.keys():
                html_content_to_send = success_page + cookies[header["Cookie"]]
            else:
                html_content_to_send = bad_creds_page
        else:
            html_content_to_send = login_page
            
            
        
        response  = 'HTTP/1.1 200 OK\r\n'
        response += headers_to_send
        response += 'Content-Type: text/html\r\n\r\n'
        response += html_content_to_send
        print_value('response', response)
        client.send(response.encode())
        client.close()

        print("Served one request/connection!")

    # We will never actually get here.
    # Close the listening socket
    sock.close()

if __name__=="__main__":
    main()