import logging
import hashlib
from flask import make_response, jsonify

logger = logging.getLogger(__name__)

def success_json_response(payload):
  """
  Turns payload into a JSON HTTP200 response
  """
  response = make_response(jsonify(payload), 200)
  response.headers["Content-type"] = "application/json"
  return response

def return_error(message):
  """
  Sends a HTTP 200 but with an error message
  """
  return success_json_response({
    "error": message
  })

def return_specific_error(message, code):
  response = make_response(message, code)
  return response

def file_md5(file):
  with open(file, "rb") as f:
    file_hash = hashlib.md5()
    while chunk := f.read(8192):
      file_hash.update(chunk)
  return file_hash.hexdigest()