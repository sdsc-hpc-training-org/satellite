use strict;
use Cwd;
use File::Basename qw(dirname); 

my $basename = dirname(Cwd::abs_path($0));

package satconfig;
# pid file for httpd. super important since we use the pid in here to 
# control httpd.
our $pidfile = '/var/run/httpd/httpd.pid';

# location of the database file
our $dbfile = $basename . '/../var/state.sqlite';

# allowed subnet for reverse-proxy targets
# format: subnet/mask
our $tgtipmask = '10.21.0.0/16';
#our $tgtipmask = '132.249.121.0/27';

# number of secs an entry can remain in 'pending' or 'mapped' state
# 'modified' field is updated when moving from pending to mapped.
# comet has a max runtime of 48h
our $ttl_secs = 600;

# the externally-facing port requests come in to
# usually the same as listenport unless DNAT is in play.
our $extport = 443;

# the name users put in their clients
our $extbasename = 'comet-user-content.sdsc.edu';

# the port apache binds to
our $listenport = 443;

# the stub file for the apache config
# it's dynamically updated by bin/cron script
our $httpdstubfile = $basename . '/../dynconf/proxyconf.conf';

1;
