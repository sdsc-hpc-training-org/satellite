use strict;
package satconfig;

# pid file for httpd. super important since we use the pid in here to 
# control httpd.
our $pidfile = '/var/tmp/pidfile';

# location of the database file
our $dbfile = '../var/state.sqlite';

# number of secs an entry can remain in 'pending' or 'mapped' state
# 'modified' field is updated when moving from pending to mapped.
# comet has a max runtime of 48h
our $ttl_secs = 600;

# the externally-facing port requests come in to
# usually the same as listenport unless DNAT is in play.
our $extport = 4080;

# the name users put in their clients
our $extbasename = 'plinky.sdsc.edu';

# the port apache binds to
our $listenport = 4080;

# the stub file for the apache config
# it's dynamically updated by bin/cron script
our $httpdstubfile = '/var/tmp/proxyconf.conf';

1;
