import string,cgi,time
import os,sys
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class SlicerRequestHandler(SimpleHTTPRequestHandler):

  def start_response(self, status, response_headers):
    self.send_response(status)
    for keyword,value in response_headers:
      self.send_header(keyword, value)
    self.end_headers()

  def logMessage(self, message):
     self.server.logMessage(message)

  def do_GET(self):
    self.protocol_version = 'HTTP/1.1'
    try:
      status = 200
      rest = self.path

      self.logMessage("Handling: " + rest)
      if os.path.dirname(rest).endswith('slicer'):
        self.logMessage('splitting path')
        rest = '/slicer/' + os.path.split(rest)[1]
      else:
        os.chdir(self.server.docroot)
        self.logMessage("Handling: " + self.path)
        SimpleHTTPRequestHandler.do_GET(self)
        return

      # talk with slicer
      if rest.find("/slicer") == 0:
        if self.server.communicatingWithSlicer:
          response_headers = [('Content-Type','text/plain')]
          self.logMessage('Server busy')
          self.start_response(status, response_headers)
          self.wfile.write( 'Busy' )
        else:
          self.server.communicatingWithSlicer = True
          subcmd = rest[len("/slicer"):]
          sys.stdout.write(subcmd + "\n")
          sys.stdout.flush()
          if subcmd.find("/repl") == 0:
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','text/plain')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/mrml") == 0:
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','application/json')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/scene") == 0:
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','application/json')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/timeimage") == 0:
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','image/png')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/slice") == 0:
            count = int(sys.stdin.readline())
            self.logMessage('trying to read %d from stdin' % count)
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','image/png')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/threeD") == 0:
            count = int(sys.stdin.readline())
            self.logMessage('trying to read %d from stdin' % count)
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','image/png')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/transform") == 0:
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','image/png')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/volumeSelection") == 0:
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','image/png')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.find("/volume") == 0:
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.logMessage("read %d from slicer" % count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','application/octet-stream')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          elif subcmd.endswith("png"):
            count = int(sys.stdin.readline())
            im = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','image/png')]
            self.start_response(status, response_headers)
            self.wfile.write( im )
          else:
            # didn't match known slicer API commands, so we shouldn't
            # prevent other slicer connections from completing
            self.logMessage('default request' % count)
            count = int(sys.stdin.readline())
            slicerResponse = sys.stdin.read(count)
            self.server.communicatingWithSlicer = False
            response_headers = [('Content-Type','text/plain')]
            self.start_response(status, response_headers)
            self.wfile.write( slicerResponse )
    except :
      self.send_error(404, "File not found")

  def do_PUT(self):
    try:
      ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
      if ctype == 'multipart/form-data':
        query=cgi.parse_multipart(self.rfile, pdict)
        self.send_response(301)
        self.end_headers()
        upfilecontent = query.get('upfile')
        # print "filecontent", upfilecontent[0]
        self.wfile.write("<HTML>PUT OK.<BR><BR>");
        self.wfile.write(upfilecontent[0]);
        xx = """
            if environ['REQUEST_METHOD'] == 'PUT':
              #TODO
              self.logMessage("got a PUT")
              body = cherrypy.request.body.read()
              self.logMessage("body is: %s" % body)
        """
    except :
        pass

    def do_POST(self):
        #TODO
        pass


class SlicerHTTPServer(HTTPServer):
  """ This runs in a process that listens for web
  requests and then communicates with slicer as a parent
  program by communicating via stdio"""
  # TODO: set header so client knows that image refreshes are needed (avoid
  # using the &time=xxx trick)
  def __init__(self, server_address=("",8070), RequestHandlerClass=SlicerRequestHandler, docroot='.', logFile=None):
    HTTPServer.__init__(self,server_address, RequestHandlerClass)
    self.docroot = docroot
    self.logFile = logFile
    # use this as a mutex on the stdio connection
    self.communicatingWithSlicer = False

  def start(self):
    """start the server
    - use one thread since we are going to communicate 
    via stdin/stdout, which will get corrupted with more threads
    """
    try:
      self.logMessage('started httpserver...')
      self.serve_forever()
    except KeyboardInterrupt:
      self.logMessage('KeyboardInterrupt - stopping')
      self.stop()

  def stop(self):
    self.socket.close()

  def logMessage(self,message):
    if self.logFile:
      fp = open(self.logFile, "a")
      fp.write(message + '\n')
      fp.close()

if __name__ == '__main__':
  if len(sys.argv) > 1:
    docroot = sys.argv[1]
  logFile = "/tmp/helper.log"
  if len(sys.argv) > 2:
    logFile = sys.argv[2]
  server = SlicerHTTPServer(docroot=docroot,logFile=logFile)
  server.start()
