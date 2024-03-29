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

# allowed host/subnet for jobstate updates
# format: subnet/mask (use /32 for host)
our $jobstateipmask = '132.249.1.1/32';

# number of secs an entry can remain in 'pending' or 'mapped' state
# 'modified' field is updated when moving from pending to mapped.
# comet has a max runtime of 48h
# set max to 49h in case job sat in queue a little long.
our $ttl_secs = 176400;

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

# nice(r) message pages go here
our $htmldir = $basename . '/../html';

# job state codes indicating a job is waiting
our @JOB_WAIT_STATE_CODES = ('CF', 'PD', 'RF', 'RH', 'RQ',
  'CONFIGURING', 'PENDING', 'REQUEUE_FED', 'REQUEUE_HOLD', 'REQUEUED');

# job state codes indicating a job is running
our @JOB_RUN_STATE_CODES = ('R', 'RUNNING');

# job state codes indicating a job is gone/exited/cancelled
our @JOB_GONE_STATE_CODES = ('BF', 'CA', 'CG', 'DL', 'F', 'NF', 'OOM',
  'PR', 'RD', 'RV', 'SI', 'SE', 'SO', 'ST', 'S', 'TO',
  'BOOT_FAIL', 'CANCELLED', 'COMPLETING', 'COMPLETED', 'DEADLINE', 'FAILED', 
  'NODE_FAIL', 'NODEFAIL' , 'OUT_OF_MEMORY', 'OUTOFMEMORY', 'PREEMPTED', 
  'RESV_DEL_HOLD', 'SIGNALING', 'SPECIAL_EXIT', 'STAGE_OUT', 'STOPPED', 
  'SUSPENDED', 'TIMEOUT');

1;
