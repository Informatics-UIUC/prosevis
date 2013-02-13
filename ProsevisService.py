#!/usr/bin/env python
#########################################################################
#
# University of Illinois/NCSA
# Open Source License
#
# Copyright (c) 2008, NCSA.  All rights reserved.
#
# Developed by:
# The Automated Learning Group
# University of Illinois at Urbana-Champaign
# http://www.seasr.org
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal with the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
# Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimers.
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimers in
# the documentation and/or other materials provided with the distribution.
#
# Neither the names of The Automated Learning Group, University of
# Illinois at Urbana-Champaign, nor the names of its contributors may
# be used to endorse or promote products derived from this Software
# without specific prior written permission.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE SOFTWARE.
#
#########################################################################

from __future__ import with_statement
import subprocess
from threading import Lock
from concurrent.futures import ThreadPoolExecutor as Pool
import cherrypy
from cherrypy import expose
import json
import shlex
import logging
import urllib
import tempfile
import os
import shutil
from socket import gethostname

###### Configuration ######

# The port the service will listen on
servicePort = 8888

# Range of ports allowed to be used for running the Meandre jobs
ports = range(10000, 20000)

# The path to the Meandre runtime executor to use
zzre = "zzre-1.4.12.jar"

# The path to Java executable
java = "java"

# Options to pass to Java
javaopts = "-Xmx7g"

###### DO NOT MODIFY BELOW THIS LINE ######

hostname = gethostname()
lock = Lock()

info = logging.getLogger(__name__).info
tmpDir = tempfile.gettempdir()

class ProsevisService(object):
    def success(self, payload):
        response = { 'status': { 'code': 0 }, 'data': payload }
        return json.dumps(response)

    def failure(self, error):
        response = { 'status': { 'code': error.args[0], 'message': error.args[1] }, 'data': None }
        return json.dumps(response)

    def execute(self, cmd, port, folder):
        global ports

        logfile = os.path.join(tmpDir, 'prosevis_%d.log' % port)
        subprocess.call(shlex.split(cmd), stdout=open(logfile, 'w'), stderr=subprocess.STDOUT)
        shutil.rmtree(folder)
        os.unlink(logfile)

        with lock:
            ports.append(port)

    def downloadFile(self, url):
        fp = urllib.urlopen(url)
        folder = tempfile.mkdtemp()
        filename = os.path.basename(url)
        out = open(os.path.join(folder, filename), 'wb')
        out.write(fp.read())
        out.close()

        return (folder, filename)

    @expose
    def submitDocument(self, url=None, email=None, token=None):
        print ("submitDocument: url=%s  email=%s  token=%s" % (url, email, token))

        missing = []
        if url is None: missing.append('url')
        if email is None: missing.append('email')
        if token is None: missing.append('token')

        if len(missing) > 0:
            return self.failure(Exception(417, "Missing required parameters: %s" % missing))

        try:
            (folder, filename) = self.downloadFile(url)
            doc = os.path.join(folder, filename)
        except IOError as ex:
            return self.failure(ex.strerror)

        global ports
        with lock:
            port = ports.pop(0)

        global java, javaopts, zzre

        cmd = '{} {} -jar {} '\
              'Service_Process_TEI_XML_through_OpenMary.mau '\
              '--port "{}" --param tei_url="{}" --param email_to="{}" --param token="{}"'.format(java, javaopts, zzre, port, doc, email, token)

        pool = Pool(max_workers=1)
        pool.submit(self.execute, cmd, port, folder)
        pool.shutdown(wait=False)

        return self.success({ 'token': token, 'console': 'http://%s:%d' % (hostname, port) })

    @expose
    def computeSimilarities(self, url=None, email=None, token=None,
                            comparison_range="all", max_phonemes_per_vol=999999999, num_rounds=1, use_sampling=False,
                            weighting_power=32.0, phonemes_window_size=8, 
                            pos_weight=1, accent_weight=1, stress_weight=1, tone_weight=1, phraseId_weight=1, phonemeId_weight=0, breakIndex_weight=1):
        print("computeSimilarities: url=%s  email=%s  token=%s" % (url, email, token))

        ###### Print request parameters (for debug purposes)
        # print("comparison_range=%s" % comparison_range)
        # print("max_phonemes_per_vol=%s" % max_phonemes_per_vol)
        # print("num_rounds=%s" % num_rounds)
        # print("use_sampling=%s" % use_sampling)
        # print("weighting_power=%s" % weighting_power)
        # print("phonemes_window_size=%s" % phonemes_window_size)
        # print("pos_weight=%s" % pos_weight)
        # print("accent_weight=%s" % accent_weight)
        # print("stress_weight=%s" % stress_weight)
        # print("tone_weight=%s" % tone_weight)
        # print("phraseId_weight=%s" % phraseId_weight)
        # print("phonemeId_weight=%s" % phonemeId_weight)
        # print("breakIndex_weight=%s" % breakIndex_weight)

        missing = []
        if url is None: missing.append('url')
        if email is None: missing.append('email')
        if token is None: missing.append('token')

        if len(missing) > 0:
            return self.failure(Exception(417, "Missing required parameters: %s" % missing))

        try:
            (folder, filename) = self.downloadFile(url)
            doc = os.path.join(folder, filename)
        except IOError as ex:
            return self.failure(ex.strerror)

        global ports
        with lock:
            port = ports.pop(0)

        global java, javaopts, zzre

        cmd = '{} {} -jar {} ' \
              'Service_Process_ZIP_TEI_XML_through_OpenMary.mau ' \
              '--port "{}" --param zip_url="{}" --param email_to="{}" --param token="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#comparison_range="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#max_phonemes_per_vol="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#num_rounds="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#use_sampling="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#weighting_power="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#phonemes_window_size="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#pos_weight="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#accent_weight="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#stress_weight="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#tone_weight="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#phraseId_weight="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#phonemeId_weight="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/prosody-similarity/11#breakIndex_weight="{}" ' \
              .format(java, javaopts, zzre, port, doc, email, token, 
                comparison_range, max_phonemes_per_vol, num_rounds, use_sampling,
                weighting_power, phonemes_window_size,
                pos_weight, accent_weight, stress_weight, tone_weight, phraseId_weight, phonemeId_weight, breakIndex_weight)

        pool = Pool(max_workers=1)
        pool.submit(self.execute, cmd, port, folder)
        pool.shutdown(wait=False)

        return self.success({ 'token': token, 'console': 'http://%s:%d' % (hostname, port) })


cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': servicePort, })
cherrypy.quickstart(ProsevisService())
