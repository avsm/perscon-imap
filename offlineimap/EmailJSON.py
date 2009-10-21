# convert an email message into a Python structure which can be JSON serialized

import email
import os
import time
import simplejson as json
import uuid

def _to_unicode(str, verbose=False):  
    '''attempt to fix non uft-8 string into utf-8, using a limited set of encodings'''  
    # fuller list of encodings at http://docs.python.org/library/codecs.html#standard-encodings  
    if not str:  return u''
    if type(str) == unicode: return str
    u = None  
    # we could add more encodings here, as warranted.  
    encodings = ('ascii', 'utf8', 'latin1')  
    for enc in encodings:  
        if u:  break  
        try: 
            u = unicode(str,enc)  
        except UnicodeDecodeError:  
            if verbose: print "error for %s into encoding %s" % (str, enc)  
            pass  
    if not u:  
        u = unicode(str, errors='replace')  
        if verbose:  print "using replacement character for %s" % str  
    return u  

def _tuple_to_unicode(t):
    return tuple(map(_to_unicode, t))

def determine_bulk(hdrs, folder):
    if folder.lower() == 'spam' or folder.lower() == 'junk':
        return True
    if 'list-id' in hdrs:
        return True
    if 'mailing-list' in hdrs:
        return True
    if 'precedence' in hdrs:
        p = hdrs['precedence'].lower()
        if p == 'list' or p == 'bulk' or p =='junk':
           return True
    if 'x-spam-flag' in hdrs:
        if hdrs['x-spam-flag'].lower() == 'yes':
           return True
    return False

def convert_mail_to_dict(content, folder, uid, flags, rtime, atts):
    mail = email.message_from_string(content)
    tos = mail.get_all('to', [])
    ccs = mail.get_all('cc', [])
    resent_tos = mail.get_all('resent-to', [])
    resent_ccs = mail.get_all('resent-cc', [])
    all_tos_str = email.utils.getaddresses(tos + ccs + resent_tos + resent_ccs)
    all_tos = map(_tuple_to_unicode, all_tos_str)
    frm = _tuple_to_unicode(email.utils.parseaddr(mail['from'])) 
    frm_ldb = [ { 's_ty' : 'email', 's_id': frm[1], 's_co': None } ]
    
    all_tos_ldb = map(lambda x: { 's_ty' : 'email', 's_id' : x[1], 's_co':None }, all_tos)
    try:
        date = email.utils.mktime_tz(email.utils.parsedate_tz(mail.get('date')))
    except:
        date = 0.0
    subject = _to_unicode(mail.get('subject',''))
    msg_id = _to_unicode(mail.get('message-id',''))
    filter_headers = ['to','cc','resent-to','resent-cc','from','subject','date', 'message-id']
    headers = filter(lambda x : str.lower(x) not in filter_headers, mail.keys())
    header_dict = dict([(h.lower(),_to_unicode(mail[h])) for h in headers])
    body = parse_mail_content(mail, atts)
    flags = str.join('', flags)
    tags = [ 'email', folder ] 
    meta = { 'flags': flags, 'subject': subject, 'date': str(date), 'folder':folder,'message-id': msg_id }
    am = map(lambda a : atts[a]['meta'], atts)
    msg = { 'e_origin':'IMAP', 'e_uid':uid, 'e_mtime':date, 'e_from': frm_ldb, 'e_to': all_tos_ldb, 'e_meta': meta, 'e_folder': folder, 'e_tags':tags, 'e_atts': am }
    return msg

def tojson(d):
    return json.dumps(d, indent=2)

def parse_mail_content(msg, atts):
    if msg.is_multipart():
       return { 'multipart': True, 'parts' : map(lambda x: parse_mail_content(x,atts), msg.get_payload()), 
          'ctype': _to_unicode(msg.get_content_type()) }
    else:
       uid = uuid.uuid4().hex
       mime = _to_unicode(msg.get_content_type())
       r = { 'mime': mime, 'multipart' : False }
       if msg.get_filename(None):
          r['filename'] = _to_unicode(msg.get_filename())
          fbasename, fext = os.path.splitext(r['filename'])
          if fext:
               uid = uid + fext
       elif mime == 'text/plain':
          uid = uid + '.txt'
       r['uuid'] = uid
       if msg.get_content_charset():
          r['charset'] = _to_unicode(msg.get_content_charset())
       att_meta = { 'a_mime' : mime, 'a_uid': uid }
       att = { 'meta' : att_meta, 'body' : msg.get_payload(decode=True) }
       atts[uid] = att
       return uid
