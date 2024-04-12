import logging
import os
from sqlitedict import SqliteDict
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from utils import success_json_response, return_error, return_specific_error, file_md5
from lov import esp_headers

ALLOWED_EXT = [ "bin" ]

app = Flask(__name__)
db = SqliteDict("kv.db")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s')
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET"])
def root():
  mac = request.headers.get("x-client-mac")
  if not mac:
    return return_error("no mac address in header")
  logger.info(f"Got request for MAC {mac}")
  device = db.get(mac)
  response = {
    "mac": mac
  }
  if not device:
    response["configured"] = "no"
  else:
    response["configured"] = "yes"
    response = {**response, **device}
  return success_json_response(response)

@app.route("/dev/<string:mac>", methods=["POST"])
def update_device(mac):
  device = db.get(mac, default = {})
  if not request.json:
    return return_error("Request should be JSON")
  db[mac] = {**device, **request.json}
  db.commit()
  return success_json_response(
    db[mac]
  )

def allowed_file(filename):
  return "." in filename and \
    filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
  if request.method == "POST":
    if "file" not in request.files:
      return '''
Failed, no file part.
'''
    file = request.files["file"]
    if file.filename == "":
      return '''
Failed, no selected file.
'''
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      if os.path.isfile(os.path.join("bin", filename)):
        return '''
Failed, file exists.
'''
      file.save(os.path.join("bin", filename))
      return f'''
Saved as {filename}
'''
  return '''
<!doctype html>
<title>Upload new File</title>
<h1>Upload new bin file</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
'''

@app.route("/update", methods=["GET"])
def update():
  # check all expected headers are present
  for header in esp_headers:
    logger.debug(f"Got value {request.headers[header]} for header {header}")
    if not header in request.headers:
      return return_specific_error("403 Forbidden", 403)
  # get mac address
  mac = request.headers.get("x-ESP8266-STA-MAC").replace(":", "-")
  logger.info(f"Got all required headers, checking for updates for {mac}")
  # lookup mac address
  device = db.get(mac, default = {})
  if device:
    if "code" in device:
      binfile = device["code"]
      logger.info(f"Checking {binfile} for device {mac}")
      server_md5 = file_md5(f"bin/{binfile}")
      logger.info(f"{binfile} md5 = {server_md5}")
      client_md5 = request.headers.get("x-ESP8266-sketch-md5")
      if server_md5 != client_md5:
        logger.info("MD5 does not match, so sending file")
        resp = send_file(
          f"bin/{binfile}", 
          mimetype="application/octet-stream",
          as_attachment=True,
          download_name=binfile
        )
        resp.headers["x-MD5"] = server_md5
        #return resp
        return return_specific_error("304 Not Modified", 304)
    else:
      logger.info("Device found, but no code key has been configured")
  else:
    logger.info("Can't find device")
      
  return return_specific_error("304 Not Modified", 304)

if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=5001, threaded=True)