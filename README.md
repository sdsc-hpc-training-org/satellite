# Satellite Reverse Proxy Service: A Jupyter Notebook Proxy

## Description
SRPS is a prototype system that allows users to launch secure standard Jupyter Notebooks on on any Expanse compute node using a reverse proxy server. Notebooks are hosted on the internal cluster network as an HTTP service using standard Jupyter commands. The service available to the user outside of the cluster firewall over HTTPS connection between the external users web browser and the reverse proxy server. The goal is to minimize software changes for our users while improving the security of user notebooks running on our HPC systems. The SRPS service is capable of running on any HPC system capable of supporting the RP server (needs Apache).

The Satellite Proxy Server system is designed to simplify the process of launching a secure Jupyter Notebook by the
client. The system consists of two main components: 
1 the Satellite Reverse Proxy Service 
2 the Jupyter Spawner Client.
This page describes the Satellite Reverse Proxy Service. For an example of an SRPS client, see the [galyleo client site](https://github.com/mkandes/galyleo).

## Notes
* These cgi scripts and configuration are intended to work with
a standard centos 7 httpd installation.

* The bundled word list comes from the eff_large_wordlist:
https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases

* Don't use /usr/share/dict/words, as users may receive urls with offensive words in them.



## Config 
Deploy the httpd-conf/*.conf files in /etc/httpd/conf.d/ and 
remove /etc/httpd/conf.d/ssl.conf.

You'll need to create
  /var/www/satellite
which has this structure:
  satellite
  satellite/html
  satellite/var
  satellite/var/words
  satellite/var/state.sqlite
  satellite/cgi-bin
  satellite/cgi-bin/getlink.cgi
  satellite/cgi-bin/index.cgi
  satellite/cgi-bin/redeemtoken.cgi
  satellite/bin
  satellite/bin/cron
  satellite/dynconf
  satellite/dynconf/proxyconf.conf
  satellite/etc
  satellite/etc/satconfig.pm

Examine satellite/etc/satconfig.pm, with careful attention to extbasename.
Examine the httpd config files similarly.
You will need a wildcard cert for extbasename, put it in /var/secrets.
The 00-ssl.conf file will point to this cert.

## Accounts
In addition to the apache account, you'll need an account to run a cron job.
That account should be added to the apache group.

## Cron
Run bin/cron every minute as the aformentioned account.  This will update the
dynconf/proxyconf.conf file and graceful-restart apache with sudo.

## Sudo
You'll need a sudoers line like this:
ssakai  ALL=(root) NOPASSWD: /usr/bin/killall -USR1 httpd

## Database schema
Satellite uses sqlite3, see/set the location of the database in 
`./etc/satconfig.pm   $dbfile`.  The default is `$basename . '/../var/state.sqlite';`.

The schema looks like this:
```
CREATE TABLE proxy ( alias text not null, alias_compare_hash text not null, modified timestamp default current_timestamp, dsthost text, dstport integer, dstpath text, state text not null);
CREATE TABLE jobstates ( jobid text primary key, state text not null, lastseen timestamp default current_timestamp);
```

## SELinux
This has been tested with SELinux in enforcing mode with targeted policy.
You'll need to make some adjustments to permissions and labeling.

` find satellite -exec ls -ladZ '{}' \;
drwxr-xr-x. root root system_u:object_r:httpd_sys_content_t:s0 satellite
drwxr-xr-x. root root system_u:object_r:httpd_sys_content_t:s0 satellite/html
drwxrwsr-x. root apache system_u:object_r:httpd_sys_rw_content_t:s0 satellite/var
-rw-r--r--. root root unconfined_u:object_r:httpd_sys_content_t:s0 satellite/var/words
-rw-rw-r--. root apache unconfined_u:object_r:httpd_sys_rw_content_t:s0 satellite/var/state.sqlite
drwxr-xr-x. root root system_u:object_r:httpd_sys_script_exec_t:s0 satellite/cgi-bin
-rwxr-xr-x. root root unconfined_u:object_r:httpd_sys_script_exec_t:s0 satellite/cgi-bin/getlink.cgi
-rwxr-xr-x. root root unconfined_u:object_r:httpd_sys_script_exec_t:s0 satellite/cgi-bin/index.cgi
-rwxr-xr-x. root root unconfined_u:object_r:httpd_sys_script_exec_t:s0 satellite/cgi-bin/redeemtoken.cgi
drwxr-xr-x. root root unconfined_u:object_r:httpd_sys_content_t:s0 satellite/bin
-rwxr-xr-x. root root unconfined_u:object_r:httpd_sys_content_t:s0 satellite/bin/cron
drwxrwxr-x. root ssakai unconfined_u:object_r:httpd_sys_content_t:s0 satellite/dynconf
-rw-rw-r--. ssakai ssakai unconfined_u:object_r:httpd_sys_content_t:s0 satellite/dynconf/proxyconf.conf
drwxr-xr-x. root root unconfined_u:object_r:httpd_sys_content_t:s0 satellite/etc
-rw-r--r--. root root unconfined_u:object_r:httpd_sys_content_t:s0 satellite/etc/satconfig.pm
`

