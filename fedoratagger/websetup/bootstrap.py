# -*- coding: utf-8 -*-
"""Setup the fedora-tagger application"""

import logging
from tg import config
from fedoratagger import model
import transaction
import commands
import tempfile
import urllib
import sqlite3
import os
import sys

def import_pkgdb_tags():
    repo = "F-16-i386-u"
    base_url = "https://admin.fedoraproject.org/pkgdb"
    url = base_url + "/lists/sqlitebuildtags/F-16-i386-u"
    f, fname = tempfile.mkstemp(suffix="-%s.db" % repo)
    urllib.urlretrieve(url, fname)

    conn = sqlite3.connect(fname)
    cursor = conn.cursor()
    cursor.execute('select * from packagetags')
    failed = []
    for row in cursor:
        name, tag, score = row
        p = model.Package.query.filter_by(name=name)
        tl = model.TagLabel.query.filter_by(label=tag)
        if p.count() == 0:
            model.DBSession.add(model.Package(name=name))

        if tl.count() == 0:
            model.DBSession.add(model.TagLabel(label=tag))

        package = p.one()
        label = tl.one()

        t = model.Tag()
        t.package = package
        t.label = label
        model.DBSession.add(t)

        if label not in package.tag_labels:
            package.tag_labels.append(label)


    conn.close()
    os.remove(fname)

    npacks = model.Package.query.count()
    ntags = model.Tag.query.count()

    # TODO -- why are there some packages in koji, but not in pkgdb?
    print "Done."
    print "Failed on:", failed
    print "Failed on:", len(failed), "packages (see above)."
    print "Imported", npacks, "packages."
    print "Imported", ntags, "tags."

def bootstrap(command, conf, vars):
    """Place any commands to setup fedoratagger here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        u = model.User()
        u.user_name = u'manager'
        u.display_name = u'Example manager'
        u.email_address = u'manager@somedomain.com'
        u.password = u'managepass'
    
        model.DBSession.add(u)
    
        g = model.Group()
        g.group_name = u'managers'
        g.display_name = u'Managers Group'
    
        g.users.append(u)
    
        model.DBSession.add(g)
    
        p = model.Permission()
        p.permission_name = u'manage'
        p.description = u'This permission give an administrative right to the bearer'
        p.groups.append(g)
    
        model.DBSession.add(p)
    
        u1 = model.User()
        u1.user_name = u'editor'
        u1.display_name = u'Example editor'
        u1.email_address = u'editor@somedomain.com'
        u1.password = u'editpass'
    
        model.DBSession.add(u1)
        model.DBSession.flush()

        import_pkgdb_tags()

        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'

    # <websetup.bootstrap.after.auth>