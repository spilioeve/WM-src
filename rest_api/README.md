# SOFIA REST API

This can be run simply using:

```
export FLASK_APP=REST_API.py
flask run
```

For running in production on a server you should first install `gunicorn` with `pip install gunicorn`.

Then, from the `rest_api` directory you should run:

```
exec gunicorn --workers 3 --bind unix:sofia.sock -m 007 wsgi
```

You will need to configure NGINX to use the config called `sofia` contained in this directory and you may need to ensure that the NGINX workers can access the `sofia.sock` file that is created. You should put the `sofia` file in `/etc/nginx/sites-available` and symlink it to `/etc/nginx/sites-enabled`. To test the NGINX config use:

```
sudo nginx -t
```

If the config is acceptable then reload NGINX with:

```
sudo nginx -s reload
```