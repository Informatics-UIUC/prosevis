CONFIGURING THE SERVICE

Edit the Configuration section of ProsevisService.py to adjust the variables as needed.
This is *required* for some variables.

RUNNING THE SERVICE

There are a number of ways that can be used to start the service. All the below are valid:
> ./ProsevisService.py     (if you made it executable with: chmod +x ProsevisService.py)
or
> python ProsevisService.py

If background execution is desired, then use:

> python ProsevisService.py 1>prosevis.log 2>&1 &

the above starts it in the background and records all it's output into the "prosevis.log" file in the same folder.

PREREQUISITES

OpenMary
--------
Need to have a local copy of OpenMary. It can be downloaded from here: http://mary.dfki.de/Download
We tested with version 4.3.1, but it may work with 5.0 as well
Edit the configuration section of ProsevisService.py to adjust where the OpenMary service is running at.

Python
------
We use python 2.7.3, but other 2.7.x version will work (3.x may work as well, but we haven't tried it)
Additionally, you need to install the following packages:
	* CherryPy -- on Ubuntu, you can install the "python-cherrypy3" package. Otherwise, you can download it from here: http://www.cherrypy.org/
	* concurrent.futures package
		if you use Python 2.7.x, you need to download and install the back port from here: http://pypi.python.org/pypi/futures
		if you use Python 3.x, the concurrent.futures package is built-in

EXECUTION LOG

When someone submits a job to the prosevis service, you can keep an eye on the job status by looking in the OS temp folder for files like "prosevis_<PORT>.log" These contain the output of the Meandre flow that's executing the request.  Those log files get deleted automatically after the job completes.  

