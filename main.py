
import webapp2
import jinja2
import time
import os
import re





# package imports
import lib.utils
import lib.dbmodels




JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),'templates')),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True)





def render_str(template, **params):
  t = JINJA_ENVIRONMENT.get_template(template)
  return t.render(params)

class WikiHandler(webapp2.RequestHandler):
    def write(self,*a,**kw):
      self.response.out.write(*a,**kw)

    def render_str(self, template, **params):
      params['user'] = self.user
      params['gray_style'] = lib.utils.gray_style
      t = JINJA_ENVIRONMENT.get_template(template)
      return t.render(params)


      
    def render(self, template, **kw):
      self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
      cookie_val = lib.utils.make_secure_val(val)
      self.response.headers.add_header('Set-Cookie', '%s=%s; Path/=' %(name, cookie_val))

    def read_secure_cookie(self, name):
      cookie_val = self.request.cookies.get(name)
      return cookie_val and lib.utils.check_secure_val(cookie_val)

    def login(self, user):
      self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
      self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
    
    def initialize(self, *a, **kw):
      webapp2.RequestHandler.initialize(self, *a, **kw)
      uid = self.read_secure_cookie('user_id')
      self.user = uid and lib.dbmodels.User.by_id(int(uid))



class Signup(WikiHandler):
  def get(self):
    next_url = self.request.headers.get('referer', '/')
    self.render('signup.html', next_url = next_url)

  def post(self):
    have_error = False
    # on post take user back to thesame page they came from
    next_url = str(self.request.get('next_url'))
    if not next_url or next_url.startswith('/login'):
      next_url = '/'

    # create user info
    self.username = self.request.get("username")
    self.password = self.request.get("password")
    self.verify = self.request.get("verify")
    self.email = self.request.get("email")
    # use dict to store params to be passed later
    params = dict(username = self.username,
                  emil = self.email)

    # validate user input and store it in dbmodels.User
    
    if not lib.utils.valid_username(self.username):
      params['error_username'] = "That's not a valid username."
      have_error = True
    elif not lib.utils.valid_username(self.password):
      params['error_password'] = "That wasnt'a valid password"

    elif self.password != self.verify:
      params['error_verify'] = "Passwords don't match"

    elif not lib.utils.valid_email(self.email):
      params['error_email'] = "That's not a valid email"

    if have_error:
      self.render('signup.html', **params)

    else:
      u = lib.dbmodels.User.by_name(self.username)
    if u:
      msg = 'That user already exists.'
      self.render('signup.html', error_username = msg)
    else:
      u = lib.dbmodels.User.register(self.username, self.password, self.email)
      u.put()
      self.login(u)
      self.redirect(next_url)


class Login(WikiHandler):
  def get(self):
    next_url = self.request.headers.get('referer', '/')
    self.render('login.html', next_url=next_url)

  def post(self):

    username = self.request.get('username')
    password = self.request.get('password')

    next_url = str(self.request.get('next_url'))
    if not next_url or next_url.startswith('/login'):
      next_url = '/'
  

    u = lib.dbmodels.User.login(username,
                            password)
    if u:
      self.login(u)
      logout = 'logout'
      self.redirect(next_url)
    else:
      msg = 'invalid login'
      self.render('login.html', error_login=msg, signup='signup')
    
class Logout(WikiHandler):
  def get(self):
    next_url = self.request.headers.get('referer', '/')
    self.logout()
    self.redirect(next_url)

# class NoSlash(Handler):
#   def get(self, path):
#     new_path = path.rstrip('/') or '/' 
#     self.redirect(new_path)

class EditPage(WikiHandler):
  def get(self, path):
    if not self.user:
      self.redirect('/login')

    v = self.request.get('v')
    p = None
    if v:
      if v.isdigit():
        p = lib.dbmodels.WikiContent.by_id(int(v), path)
      if not p:
        return self.notfound()
    else:
      p = lib.dbmodels.WikiContent.by_path(path).get()

    self.render("edit.html", path = path, page = p)

  def post(self, path):
    if not self.user:
      self.error(400) 
      return
    authorname = self.user.name
    content = self.request.get('content')
    old_page = lib.dbmodels.WikiContent.by_path(path).get()
    if not(old_page or content):
      return #some error message
    elif not old_page or old_page.content != content:
      p = lib.dbmodels.WikiContent(parent = lib.dbmodels.WikiContent.parent_key(path),
                                   content = content,
                                   authorname = authorname)
      p.put()
    time.sleep(3)
    self.redirect(path)


class HistoryPage(WikiHandler):
  def get(self, path):
    q = lib.dbmodels.WikiContent.by_path(path)
    q.fetch(limit = 100)

    posts = list(q)
    if posts:
      self.render("history.html", path = path, posts = posts)
    else:
      self.redirect("/_edit" + path)



class WikiPage(WikiHandler):
  def get(self, path):
    #decides weather you're viewing old or new version of the page
    v = self.request.get('v')
    p = None
    if v:
      if v.isdigit():
        p = lib.dbmodels.WikiContent.by_id(int(v), path)
      if not p:
        return self.notfound()
    else:
      p = lib.dbmodels.WikiContent.by_path(path).get()
    if p:
      self.render("wikifront.html", page = p, path = path)
    else:
      self.redirect("/_edit" + path)

PAGE_RE =  r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
                               ('/signup', Signup),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/_history' + PAGE_RE, HistoryPage),
                               ('/_edit' + PAGE_RE, EditPage),
                               (PAGE_RE, WikiPage),
                               ],
                              debug=True)
