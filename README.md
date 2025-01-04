## Simple server with file upload capabilities

This extension of standard python webserver allows upload of (possibly signed) files to a server via web interface (`upload.html`) or curl.

All uploads (including unsuccessfull unauthorized attempts) are logged to a `uploads.log` file. Each entry has time, size, hash, original (suggested by the uploader) file name and (for successful uploads) a randomly generated file name of the uploaded file.

### Start

```
python3 server.py [PORT [upload_directory]]
```

Example:

```
python3 server.py 9081 ./uploads
```
This will listen on port 9081 and place uploaded files into ./uploads directory.

### Upload via `curl`

