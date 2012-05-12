#from __future__ import with_statement
from sys import exit
from fabric.api import env, run, local, task, settings, sudo
from fabric.contrib.files import exists
import re, os

@task
def clone(deployconf, timestr):
	arun('git clone -b {0} {1} {2}{3}'.format(deployconf['branch'], deployconf['repository_uri'], deployconf['site_dir'], timestr))
	arun('(cd {0}{1} && git submodule update --init --recursive)'.format(deployconf['site_dir'], timestr))

@task
def config(deployconf, timestr):
	for f in deployconf['configs']:
		run('ln -s {0}{1}/{2} {0}{3}/{2}'.format(deployconf['site_dir'], deployconf['config_dir'], f, timestr))

@task
def delete(deployconf, timestr):
	for f in deployconf['delete']:
		run('rm -rf {0}{1}/{2}'.format(deployconf['site_dir'], timestr, f))

@task
def links(deployconf, timestr):
	for k, v in deployconf['link'].iteritems():
		if (re.match('^\/.*', k)):
			# Absolute path
			run('ln -s {0} {1}{2}/{3}'.format(k, deployconf['site_dir'], timestr, v))
		else:
			# Relative path
			run('ln -s {0}{1} {0}{2}/{3}'.format(deployconf['site_dir'], k, timestr, v))
	
@task
def current_link(deployconf, timestr):
	linkname = '{0}{1}'.format(deployconf['site_dir'], deployconf['current_dir'])
	if (os.path.exists(linkname)):
		run('rm {0}'.format(linkname))
	run('ln -s {0}{1} {2}'.format(deployconf['site_dir'], timestr, linkname))

@task
def services(deployconf, timestr):
	run('php -r "apc_clear_cache(); apc_clear_cache(\'user\'); apc_clear_cache(\'opcode\');"');
	sudo('service php5-fpm restart');

def arun(cmd):
	"""
	Alias run command to do SSH Agent forwarding
	This just passes through the ssh client, with the -A option to allow ssh agent forwarding.
	"""
	for h in env.hosts:
		try:
			host, port = h.split(':')
			local('ssh -p %s -A %s "%s"' % (port, host, cmd))
		except ValueError:
			local('ssh -A %s "%s"' % (h, cmd))

def init_environments(environments):
	"""
	Do a merge of the environment settings on top of the __base__ configuration
	"""
	for k, v in environments.iteritems():
		if k is not '__base__':
			environments[k] = dict(environments['__base__'], **v)
	return environments

def get_environment(name, environments):
	if name is not None:
		return name
	for name, s in environments.iteritems():
		if name is not '__base__' and s['default'] is True:
			return name

	print 'You fail so hard. You need to configure a default environment, or specify one like so:'
	print '   $ fab deploy:environment=production'
	exit(1)

def openenvfile(file):
	return open(re.sub(r'\.pyc?$', '.json', os.path.basename(file)), 'r')
