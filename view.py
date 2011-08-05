#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" ``RequestHandler``s.
"""

import cgi
import logging

from pytz.gae import pytz

from google.appengine.api import mail, users
from google.appengine.ext import blobstore, db

from weblayer import RequestHandler
from weblayer.utils import unicode_urlencode

import auth
import model

class BlobStoreUploadHandler(RequestHandler):
    """ Base class for handlers that accept multiple named file uploads.
    """
    
    def __init__(self, *args, **kwargs):
        super(BlobStoreUploadHandler, self).__init__(*args, **kwargs)
        self._uploads = None
        
    
    def get_uploads(self):
        if self._uploads is None:
            self._uploads = {}
            for key, value in self.request.params.items():
                if isinstance(value, cgi.FieldStorage):
                    if 'blob-key' in value.type_options:
                        value = blobstore.parse_blob_info(value)
                        self._uploads[key] = value
        return self._uploads
        
    
    


class Index(RequestHandler):
    """
    """
    
    def get(self):
        return self.render('index.tmpl')
        
    
    


class Standard(RequestHandler):
    """
    """
    
    def get(self):
        return self.render('standard.tmpl')
        
    
    


class Download(RequestHandler):
    """
    """
    
    def get(self):
        return self.render('download.tmpl')
        
    
    


class Support(RequestHandler):
    """
    """
    
    def get(self):
        return self.render('support.tmpl')
        
    
    


class Contact(RequestHandler):
    """
    """
    
    def get(self):
        return self.render('contact.tmpl')
        
    
    


class Library(RequestHandler):
    """
    """
    
    def get(self, name=None):
        
        # Get all `Series` so we can populate the category navigation and
        # the target `Series` if one has been selected.
        series = model.Series.get_all()
        if name is None:
            target = None
        else:
            target = model.Series.get_by_key_name(name)
        
        # Get either the most recent 9 `Design`s or the `Design`s in the
        # target `Series`.
        if target is None:
            query = model.Design.all().filter("status =", u'approved')
            designs = query.order('-m').fetch(9)
        else:
            designs = target.designs
        
        # Render the template.
        return self.render(
            'library.tmpl', 
            series=series, 
            target=target, 
            designs=designs
        )
        
    
    


class AddDesign(BlobStoreUploadHandler):
    """
    """
    
    __all__ = ['get', 'post']
    
    def notify(self, design):
        """ Notify the moderators.
        """
        
        url = self.request.host_url
        user = users.get_current_user()
        
        sender = user.email()
        subject = u'New design submitted to WikiHouse.'
        body = u'Please moderate the submission:\n\n%s/moderate\n' % url
        message = mail.EmailMessage(sender=sender, subject=subject, body=body)
        
        recipients = self.settings['moderation_notification_email_addresses']
        for item in recipients:
            message.to = item
            message.send()
            
        
    
    
    @auth.required
    def post(self):
        
        attrs = {}
        error = u''
        
        params = self.request.params
        uploads = self.get_uploads()
        
        attrs['title'] = params.get('title')
        attrs['description'] = params.get('description')
        
        series = params.getall('series')
        keys = [db.Key.from_path('Series', item) for item in series]
        instances = model.Series.get(keys)
        if None in instances:
            i = instances.index(None)
            error = u'Series `%s` does not exist.' % series[i]
        attrs['series'] = keys
        
        country_code = self.request.headers.get('X-AppEngine-Country', 'GB')
        try:
            country = pytz.country_names[country_code.lower()]
        except KeyError:
            country = country_code
        attrs['country'] = country
        
        attrs.update(uploads)
        try:
            design = model.Design(**attrs)
            design.put()
        except db.Error, err:
            error = unicode(err)
        
        if error:
            data = unicode_urlencode({'error': error})
            response = self.redirect('/library/add_design/error?%s' % data)
        else:
            response = self.redirect('/library/add_design/success/%s' % design.key().id())
            self.notify(design)
        
        response.body = ''
        return response
        
    
    
    @auth.required
    def get(self):
        series = model.Series.get_all()
        upload_url = blobstore.create_upload_url(self.request.path)
        return self.render('add.tmpl', upload_url=upload_url, series=series)
        
    
    

class AddDesignSuccess(RequestHandler):
    """
    """
    
    @auth.required
    def get(self, id):
        return 'success: /library/design/%s' % id
        
    
    

class AddDesignError(RequestHandler):
    """
    """
    
    @auth.required
    def get(self):
        return 'error: %s' % self.request.params.get('error')
        
    
    


class Moderate(RequestHandler):
    
    __all__ = ['get', 'post']
    
    @auth.admin
    def post(self):
        params = self.request.params
        action = params.get('action')
        design = model.Design.get_by_id(int(params.get('id')))
        if action == 'Approve':
            design.status = u'approved'
        elif action == 'Reject':
            design.status = u'rejected'
        design.put()
        return self.get()
        
    
    
    @auth.admin
    def get(self):
        query = model.Design.all().filter("status =", u'pending')
        designs = query.order('-m').fetch(99)
        return self.render('moderate.tmpl', designs=designs)
    
    


class Design(RequestHandler):
    """
    """
    
    def get(self, id):
        target = model.Design.get_by_id(int(id))
        series = model.Series.get_all()
        return self.render(
            'design.tmpl', 
            target=target, 
            series=series 
        )
        
    
    


class NotFound(RequestHandler):
    """
    """
    
    def get(self):
        return self.render('errors/404.tmpl')
        
    
    


