from google.appengine.ext import db

import lib.utils



class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    

    @classmethod
    def by_id(cls, uid):
        return cls.get_by_id(uid, parent=lib.utils.users_key())
    @classmethod
    def by_name(cls,name):
        u = cls.all().filter('name =', name).get()
        return u
    @classmethod
    def register(cls, name, pw, email=None):
        #prepare new user object for db write
        pw_hash = lib.utils.make_pw_hash(name,pw)
        return cls(parent = lib.utils.users_key(),
                   name = name,
                   pw_hash = pw_hash,
                   email = email,
                   authorname = name)
    
    @classmethod
    def login(cls, name, pw):
        #check if the name exists in db and validate user input
        u = cls.by_name(name)
        if u and lib.utils.valid_pw(name, pw, u.pw_hash):
            return u

class WikiContent(db.Model):
    content = db.TextProperty()
    #authorname = db.ReferenceProperty(User)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    # title = db.StringProperty(required=False)
    
    @staticmethod
    def parent_key(path):
        return db.Key.from_path('/root' + path, 'pages')

    @classmethod
    def by_path(cls, path):
        q = cls.all()
        q.ancestor(cls.parent_key(path))
        q.order("-created")
        return q

    @classmethod
    def by_id(cls, page_id, path):
        return cls.get_by_id(page_id, cls.parent_key(path))

    # @classmethod
    # def by_title(cls,title):
    #     u = cls.all().ancestor(lib.utils.wiki_key()).filter('title =', title).get()
    #     return u
    # @classmethod
    # def prepare_content(cls, author_name, content, title):
    #     return cls(parent = lib.utils.wiki_key(),
    #                content = content,
    #                authorname = author_name,
    #                title = title)


    
    