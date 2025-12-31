"""
Module for maintaining code restriction patterns.
"""

import re


CODE_RESTRICTION_REGEX = [
    r"\b__import__.*\b",
    r"(\bimport os\b)|(\bfrom os import.*)",
    r"(\bfrom django.conf import settings\b)",
    r"(\bimport shutil\b)|(\bfrom shutil import.*)",
    r"(\bimport memoryview\b)|(\bfrom memoryview import.*)",
    r"(\bimport threading\b)|(\bfrom threading import.*)",
    r"(\bimport mutiprocessing\b)|(\bfrom mutiprocessing import.*)",
    r"(\bimport sched\b)|(\bfrom sched import.*)",
    r"(\bimport mutex\b)|(\bfrom mutex import.*)",
    r"(\bimport fileinput\b)|(\bfrom fileinput import.*)",
    r"(\bimport stat\b)|(\bfrom stat import.*)",
    r"(\bimport statvfs\b)|(\bfrom statvfs import.*)",
    r"(\bimport filecmp\b)|(\bfrom filecmp import.*)",
    r"(\bimport tempfile\b)|(\bfrom tempfile import.*)",
    r"(\bimport dircache\b)|(\bfrom dircache import.*)",
    r"(\bimport mcpath\b)|(\bfrom mcpath import.*)",
    r"(\bimport pickle\b)|(\bfrom pickle import.*)",
    r"(\bimport cPickle\b)|(\bfrom cPickle import.*)",
    r"(\bimport shelve\b)|(\bfrom shelve import.*)",
    r"(\bimport marshal\b)|(\bfrom marshal import.*)",
    r"(\bimport anydbm\b)|(\bfrom anydbm import.*)",
    r"(\bimport whichdb\b)|(\bfrom whichdb import.*)",
    r"(\bimport dbm\b)|(\bfrom dbm import.*)",
    r"(\bimport gdbm\b)|(\bfrom gdbm import.*)",
    r"(\bimport dbhash\b)|(\bfrom dbhash import.*)",
    r"(\bimport bsddb\b)|(\bfrom bsddb import.*)",
    r"(\bimport dubdbm\b)|(\bfrom dubdbm import.*)",
    r"(\bimport sqlite3\b)|(\bfrom sqlite3 import.*)",
    r"(\bimport zlib\b)|(\bfrom zlib import.*)",
    r"(\bimport gzip\b)|(\bfrom gzip import.*)",
    r"(\bimport bz2\b)|(\bfrom bz2 import.*)",
    r"(\bimport zipfile\b)|(\bfrom zipfile import.*)",
    r"(\bimport tarfile\b)|(\bfrom tarfile import.*)",
    r"(\bimport Configparser\b)|(\bfrom Configparser import.*)",
    r"(\bimport robotparser\b)|(\bfrom robotparser import.*)",
    r"(\bimport netrc\b)|(\bfrom netrc import.*)",
    r"(\bimport xdrlib\b)|(\bfrom xdrlib import.*)",
    r"(\bimport plistlib\b)|(\bfrom plistlib import.*)",
    r"(\bimport io\b)|(\bfrom io import.*)",
    r"(\bimport getpass\b)|(\bfrom getpass import.*)",
    r"(\bimport curses\b)|(\bfrom curses import.*)",
    r"(\bimport platform\b)|(\bfrom platform import.*)",
    r"(\bimport errno\b)|(\bfrom errno import.*)",
    r"(\bimport ctypes\b)|(\bfrom ctypes import.*)",
    r"(\bimport select\b)|(\bfrom select import.*)",
    r"(\bimport thread\b)|(\bfrom thread import.*)",
    r"(\bimport dummy_threading\b)|(\bfrom dummy_threading import.*)",
    r"(\bimport dummy_thread\b)|(\bfrom dummy_thread import.*)",
    r"(\bimport mmap\b)|(\bfrom mmap import.*)",
    r"(\bimport readline\b)|(\bfrom readline import.*)",
    r"(\bimport rlcompleter\b)|(\bfrom rlcompleter import.*)",
    r"(\bimport subprocess\b)|(\bfrom subprocess import.*)",
    r"(\bimport socket\b)|(\bfrom socket import.*)",
    r"(\bimport ssl\b)|(\bfrom ssl import.*)",
    r"(\bimport signal\b)|(\bfrom signal import.*)",
    r"(\bimport popen2\b)|(\bfrom popen2 import.*)",
    r"(\bimport asyncore\b)|(\bfrom asyncore import.*)",
    r"(\bimport asynchat\b)|(\bfrom asynchat import.*)",
    r"(\bimport email\b)|(\bfrom email import.*)",
    r"(\bimport mailcap\b)|(\bfrom mailcap import.*)",
    r"(\bimport mailbox\b)|(\bfrom mailbox import.*)",
    r"(\bimport mhlip\b)|(\bfrom mhlip import.*)",
    r"(\bimport mimetools\b)|(\bfrom mimetools import.*)",
    r"(\bimport Mimewriter\b)|(\bfrom Mimewriter import.*)",
    r"(\bimport mimify\b)|(\bfrom mimify import.*)",
    r"(\bimport multifile\b)|(\bfrom multifile import.*)",
    r"(\bimport binhex\b)|(\bfrom binhex import.*)",
    r"(\bimport binascii\b)|(\bfrom binascii import.*)",
    r"(\bimport quopri\b)|(\bfrom quopri import.*)",
    r"(\bimport uu\b)|(\bfrom uu import.*)",
    r"(\bimport HTMLParser\b)|(\bfrom HTMLParser import.*)",
    r"(\bimport sgmllib\b)|(\bfrom sgmllib import.*)",
    r"(\bimport htmllib\b)|(\bfrom htmllib import.*)",
    r"(\bimport xml\b)|(\bfrom xml import.*)",
    r"(\bimport webbrowser\b)|(\bfrom webbrowser import.*)",
    r"(\bimport cgi\b)|(\bfrom cgi import.*)",
    r"(\bimport cgitb\b)|(\bfrom cgitb import.*)",
    r"(\bimport wsgiref\b)|(\bfrom wsgiref import.*)",
    r"(\bimport ftplib\b)|(\bfrom ftplib import.*)",
    r"(\bimport imaplib\b)|(\bfrom imaplib import.*)",
    r"(\bimport poplib\b)|(\bfrom poplib import.*)",
    r"(\bimport nntplib\b)|(\bfrom nntplib import.*)",
    r"(\bimport smtplib\b)|(\bfrom smtplib import.*)",
    r"(\bimport SocketServer\b)|(\bfrom SocketServer import.*)",
    r"(\bimport BaseHTTPServer\b)|(\bfrom BaseHTTPServer import.*)",
    r"(\bimport SimpleHTTPServer\b)|(\bfrom SimpleHTTPServer import.*)",
    r"(\bimport CGIHTTPServer\b)|(\bfrom CGIHTTPServer import.*)",
    r"(\bimport cookielib\b)|(\bfrom cookielib import.*)",
    r"(\bimport Cookie\b)|(\bfrom Cookie import.*)",
    r"(\bimport xmlrpclib\b)|(\bfrom xmlrpclib import.*)",
    r"(\bimport SimpleXMLRPCServer\b)|(\bfrom SimpleXMLRPCServer import.*)",
    r"(\bimport DocXMLRPCServer\b)|(\bfrom DocXMLRPCServer import.*)",
    r"(\bimport audioop\b)|(\bfrom audioop import.*)",
    r"(\bimport imageop\b)|(\bfrom imageop import.*)",
    r"(\bimport aifc\b)|(\bfrom aifc import.*)",
    r"(\bimport sunau\b)|(\bfrom sunau import.*)",
    r"(\bimport wave\b)|(\bfrom wave import.*)",
    r"(\bimport chunk\b)|(\bfrom chunk import.*)",
    r"(\bimport colorsys\b)|(\bfrom colorsys import.*)",
    r"(\bimport imghdr\b)|(\bfrom imghdr import.*)",
    r"(\bimport sndhdr\b)|(\bfrom sndhdr import.*)",
    r"(\bimport ossaudiodev\b)|(\bfrom ossaudiodev import.*)",
    # r"(\bimport gettext\b)|(\bfrom gettext import.*)",
    # r"(\bimport locale\b)|(\bfrom locale import.*)",
    r"(\bimport cmd\b)|(\bfrom cmd import.*)",
    r"(\bimport shlex\b)|(\bfrom shlex import.*)",
    r"(\bimport distutils\b)|(\bfrom distutils import.*)",
    r"(\bimport ensurepip\b)|(\bfrom ensurepip import.*)",
    r"(\bimport code\b)|(\bfrom code import.*)",
    r"(\bimport codeop\b)|(\bfrom codeop import.*)",
    r"(\bimport py_compile\b)|(\bfrom py_compile import.*)",
    r"(\bimport compileall\b)|(\bfrom compileall import.*)",
    r"(\bimport dis\b)|(\bfrom dis import.*)",
    r"(\bimport termios\b)|(\bfrom termios import.*)",
    r"(\bimport tty\b)|(\bfrom tty import.*)",
    r"(\bimport pty\b)|(\bfrom pty import.*)",
    r"(\bimport commands\b)|(\bfrom commands import.*)",
]


def validate_imports(code):
    result = []
    if not code:
        return result
    for regex_pattern in CODE_RESTRICTION_REGEX:
        matches = re.finditer(regex_pattern, code, re.IGNORECASE)
        for m in matches:
            match_start_index = m.start(0)
            current_line_number = len(code[:match_start_index].split("\n"))

            # Check for line is commented or not
            current_line_content = code.split("\n")[current_line_number - 1]
            if not str(current_line_content).strip().startswith("#"):
                result.append(
                    {
                        "line": current_line_number,
                        "error": "This import/function usage is not allowed.",
                    }
                )
    return result
