# Django Social Network

A social media web-application with Django.

## Features :

<li>Sign Up, Login, OAuth 2.0(Google, Github), Logout, Forgot Password</li>
<li>Public Profile view</li>
<li>Create, Edit, Delete Posts with customized text, pictures and links</li>
<li>Like, Comment / Reply, Save and Search posts</li>
<li>Follow and Unfollow users to view their posts</li>
<li>Friend Request</li>
<li>Notifications</li>
<li>Chats using websockets</li>
<li>Video Calls</li>

## Installation

### Ensure you're running Python 3.11+

### Adding env variables

- Add env variables to ".test.env" and rename it to ".env"

- Add GOOGLE_RECAPTCHA_SECRET_KEY to both .env and the file mentioned below https://github.com/Ronik22/Django_Social_Network_App/blob/main/users/templates/users/register.html#L45

- Add agora app_id to .env and to https://github.com/Ronik22/Django_Social_Network_App/blob/main/blog/static/blog/js/streams.js#L2

### Add django-allauth config

https://django-allauth.readthedocs.io/en/latest/installation.html#post-installation

### Run commands to stand up the server

```bash
    $ sudo apt-get install build-essential autoconf libtool libffi-dev pkg-config python3-dev python3-setuptools python3-testresources
    $ python -m venv venv
    $ source venv/bin/activate
    (venv) pip install -r requirements.txt
    (venv) python manage.py makemigrations
    (venv) python manage.py migrate
    (venv) python manage.py createsuperuser
    (venv) python manage.py collectstatic
    (venv) python manage.py runserver
```


### Accessory instructions

- To use other DB edit this settings.py#L107
- To use other providers edit this settings.py#L205
- To use redis instead edit this settings.py#L197

## Running Tests

To run tests, run the following command

```bash
  python manage.py test
```

## Deploy to Heroku

https://devcenter.heroku.com/articles/getting-started-with-python

https://realpython.com/django-hosting-on-heroku/