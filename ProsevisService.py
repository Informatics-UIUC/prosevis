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
import sys
import shutil
import socket

###### Configuration ######

# The name of this host (must be visible on the internet) - determined automatically, but in rare cases must be manually specified
hostname = socket.gethostname()

# The port the service will listen on
servicePort = 8888

# Range of ports allowed to be used for running the Meandre jobs
ports = range(10000, 20000)

# The path to the Meandre runtime executor to use
zzre = "zzre-1.4.12.jar"

# The path to Java executable
java = "java"

# Options to pass to Java
javaopts = "-Xmx4g"

# OpenMary configuration
openmary_hostname = "localhost"
openmary_port = 59125

# SMTP configuration
smtp_server = "YOU MUST CHANGE THIS"
email_from = "meandre@seasr.org"
email_subject = "Job results for: %s"  # %s here refers to the job token

# Result configuration
www_documentroot = "/var/www/"  # needs to be a path (must end with /) for the WWW DocumentRoot; this is the path that the web server uses to serve documents from
result_relative_location_regex = www_documentroot + "(.+)"  # this regex extracts the relative path of the result to the www documentroot; you should not need to change this
result_path = www_documentroot + "seasr/prosevis/results/"  # this is where results will be written; make sure that the user under which the prosevis service will be running has permission to write to this folder

# Email templates for the result email (BE CAREFUL WHEN MODIFYING! make sure you preserve the %s in the format, which is a placeholder for the errors or the result location)
result_error_email_template = "Note: This is an automatically generated email - do not reply!\n\nUnfortunately your document did not process successfully. Please see below for the error encountered:\n\n%s\n\nSorry for any inconvenience."
result_success_email_template = "Note: This is an automatically generated email - do not reply!\n\nYour document has been successfully processed. You can access your results at the following link:\nhttp://{}/%s\n\nThank you.\n".format(hostname)

# XSL locations
xsl_add_seasr_id = os.path.join("xsl", "add-seasr-id.xsl")
xsl_lg_to_p = os.path.join("xsl", "lg-to-p.xsl")
xsl_preprocess = os.path.join("xsl", "tei-to-document-idonly-concatlg.xsl")
xsl_mary_to_csv = os.path.join("xsl", "mary-to-csv.xsl")

###### DO NOT MODIFY BELOW THIS LINE ######

lock = Lock()

info = logging.getLogger(__name__).info
tmpDir = tempfile.gettempdir()

def isOpen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False

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

        cmd = '{} {} -jar {} ' \
              'Service_Process_TEI_XML_through_OpenMary.mau ' \
              '--port "{}" --param tei_url="{}" --param email_to="{}" --param token="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/push-text/1#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/push-text/6#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/push-text/13#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/push-text/19#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/openmary-client/31#server_hostname="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/openmary-client/31#server_port="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/text-format/3#format="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/text-format/2#format="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/send-email/8#smtp_server="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/push-text/3#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/text-format/7#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/write-to-archive/0#default_folder="{}" ' \
              '--param meandre://seasr.org/services/service-process-tei-xml-through-openmary/instance/search-text/1#expression="{}" ' \
              .format(java, javaopts, zzre, port, doc, email, token, 
                xsl_add_seasr_id, xsl_lg_to_p, xsl_preprocess, xsl_mary_to_csv,
                openmary_hostname, openmary_port,
                result_error_email_template, result_success_email_template,
                smtp_server, email_from, email_subject,
                result_path, result_relative_location_regex)

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

        cmd = '{} {} -jar {} ' \
              'Service_Process_ZIP_TEI_XML_through_OpenMary.mau ' \
              '--port "{}" --param zip_url="{}" --param email_to="{}" --param token="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/push-text/1#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/push-text/6#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/push-text/13#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/push-text/19#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/openmary-client/31#server_hostname="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/openmary-client/31#server_port="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/text-format/3#format="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/text-format/2#format="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/send-email/8#smtp_server="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/push-text/3#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/text-format/7#message="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/write-to-archive/0#default_folder="{}" ' \
              '--param meandre://seasr.org/services/service-process-zip-tei-xml-through-openmary/instance/search-text/1#expression="{}" ' \
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
                xsl_add_seasr_id, xsl_lg_to_p, xsl_preprocess, xsl_mary_to_csv,
                openmary_hostname, openmary_port,
                result_error_email_template, result_success_email_template,
                smtp_server, email_from, email_subject,
                result_path, result_relative_location_regex,
                comparison_range, max_phonemes_per_vol, num_rounds, use_sampling,
                weighting_power, phonemes_window_size,
                pos_weight, accent_weight, stress_weight, tone_weight, phraseId_weight, phonemeId_weight, breakIndex_weight)

        pool = Pool(max_workers=1)
        pool.submit(self.execute, cmd, port, folder)
        pool.shutdown(wait=False)

        return self.success({ 'token': token, 'console': 'http://%s:%d' % (hostname, port) })

# Sanity checks

if not os.path.isdir(result_path):
    print >> sys.stderr, "ProseVis result location folder does not exist - attempting to create"
    os.makedirs(result_path)

if not os.path.exists(zzre):
    print >> sys.stderr, "Could not find required Meandre execution runtime file: " + zzre
    sys.exit(-1)

if not os.path.exists(xsl_add_seasr_id) or \
   not os.path.exists(xsl_lg_to_p) or \
   not os.path.exists(xsl_preprocess) or \
   not os.path.exists(xsl_mary_to_csv):
   print >> sys.stderr, "One of the required XSL files could not be found. Cannot continue."
   sys.exit(-2)

if not isOpen(openmary_hostname, openmary_port):
    print >> sys.stderr, "OpenMary is not running. Please start OpenMary before starting the ProseVis service. Exiting..."
    sys.exit(-3)

# Start the service
cherrypy.config.update({'server.socket_host': hostname, 'server.socket_port': servicePort, })
cherrypy.quickstart(ProsevisService())
