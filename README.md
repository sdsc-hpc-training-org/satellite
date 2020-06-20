# Satellite: A Jypyter Notebook Proxy

## Notes
These cgi scripts and configuration are intended to work with
a standard centos 7 httpd installation.

The bundled word list comes from the eff_large_wordlist:
https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases

Don't use /usr/share/dict/words, as users may receive urls with offensive words in them.

Non-Default Packages:
  perl-Net-IP
  
## Config 
Deploy the httpd-conf/httpd.conf file in /etc/httpd/conf/
It will override existing httpd configs.

You'll need to create
`  /var/www/satellite `
which has this structure:
```
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
```

Examine satellite/etc/satconfig.pm, with careful attention to extbasename.
Examine the httpd config files similarly.
You will need a wildcard cert for extbasename, put it in /var/secrets.
The ssl section of httpd.conf file will point to this cert.


## State
Ensure that satellite/var is accessible by the web server and nobody else.
Ensure that satellite/var is writable by the web server and nobody else.
`chown root:apache var`
`chmod 2770 var`

Create the sqlite db as follows:
```echo 'CREATE TABLE proxy ( alias text not null, alias_compare_hash text not null, modified timestamp default current_timestamp, dsthost text, dstport integer, dstpath text, state text not null);' | sudo sqlite3 satellite/var/state.sqlite
chown apache:apache satellite/var/state.sqlite
chown 0600 satellete/var/state.sqlie
```

Ensure that satellite/dynconf is accessible by root and nobody else.
It will contain soft-secrets (the urls for notebooks)
`chown root:root dynconf`
`chmod 0700 dynconf`

Finally, create an empty file: satellite/dynconf/proxyconf.conf

Give things a kick by running bin/cron as root.


## Cron
Run bin/cron every minute as root.  This will update the
dynconf/proxyconf.conf file and graceful-restart apache.


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

