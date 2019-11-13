=Satellite: A Jypyter Notebook Proxy=

== Notes ==
These cgi scripts and configuration are intended to work with
a standard centos 7 httpd installation.

== Config ==
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

== Accounts ==
In addition to the apache account, you'll need an account to run a cron job.
That account should be added to the apache group.

== Cron ==
Run bin/cron every minute as the aformentioned account.  This will update the
dynconf/proxyconf.conf file and graceful-restart apache with sudo.

== Sudo ==
You'll need a sudoers line like this:
ssakai  ALL=(root) NOPASSWD: /usr/bin/killall -USR1 httpd


== SELinux ==
This has been tested with SELinux in enforcing mode with targeted policy.
You'll need to make some adjustments to permissions and labeling.

# find satellite -exec ls -ladZ '{}' \;
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
#

