use strict;
use Cwd;
use File::Basename qw(dirname); 

my $basename = dirname(Cwd::abs_path($0));

package satconfig;
# pid file for httpd. super important since we use the pid in here to 
# control httpd.
our $pidfile = '/var/run/httpd/httpd.pid';

# location of the database file
# our $dbfile = defined $ENV{'SAT_CONFIG_DBFILE'} ? $ENV{'SAT_CONFIG_DBFILE'} : $basename . '/../var/state.sqlite';
# setting this via env is difficult since many services clean out their environment
our $dbfile = '/var/secrets/satellite-state/state.sqlite';

# allowed subnet for reverse-proxy targets
# format: subnet/mask
our $tgtipmask = defined $ENV{'SAT_CONFIG_TGTIPMASK'} ? $ENV{'SAT_CONFIG_TGTIPMASK'} : '10.0.0.0/8';

# allowed host/subnet for jobstate updates
# format: subnet/mask (use /32 for host)
# anyone on an allowed host can push a jobstate update, be as specific as practical here
our $jobstateipmask = defined $ENV{'SAT_CONFIG_JOBSTATEIPMASK'} ? $ENV{'SAT_CONFIG_JOBSTATEIPMASK'} : '10.1.1.1/32';

# number of secs an entry can remain in 'pending' or 'mapped' state
# 'modified' field is updated when moving from pending to mapped.
# comet has a max runtime of 48h
# set max to 49h in case job sat in queue a little long.
our $ttl_secs = defined $ENV{'SAT_CONFIG_TTL_SECS'} ? $ENV{'SAT_CONFIG_TTL_SECS'} : 176400;

# the externally-facing port requests come in to
# usually the same as listenport unless DNAT is in play.
our $extport = defined $ENV{'SAT_CONFIG_EXTPORT'} ? $ENV{'SAT_CONFIG_EXTPORT'} : 443;

# the name users put in their clients
our $extbasename = defined $ENV{'SAT_CONFIG_EXTBASENAME'} ? $ENV{'SAT_CONFIG_EXTBASENAME'} : 'satellite.example.com';

# the port apache binds to
our $listenport = defined $ENV{'SAT_CONFIG_LISTENPORT'} ? $ENV{'SAT_CONFIG_LISTENPORT'} : 443;

# the stub file for the apache config
# it's dynamically updated by bin/cron script
#our $httpdstubfile = defined $ENV{'SAT_CONFIG_HTTPDSTUBFILE'} ? $ENV{'SAT_CONFIG_HTTPDSTUBFILE'} : $basename . '/../dynconf/proxyconf.conf';
# setting via env is difficult because many services clean out their environment.
our $httpdstubfile = '/var/secrets/proxyconf.conf';

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

# unix group for revssh account pool
# CAUTION: DO NOT PUT USER ACCOUNTS IN THIS GROUP
# ACCOUNTS IN THIS GROUP WILL BE HANDED TO ANONYMOUS USERS OF
# SATELLITE
# This group must have enough groups to satisfy the peak number 
# of concurrent sessions and then some for abandoned sessions.
our $revssh_group = 'revssh';

# chroot directory for revssh sockets
# This directory should live on persistent storage.
# This directory must be owned by root, not writable by non-root.
# This directory must contain directories for each account in revssh_group,
#   which in turn are also owned by root.
# Each account directory must contain a "socket" directory, owned and only writable by the account.
# e.g 
#   root:root 0755   $revssh_chroot_dir
#   root:root 0755   $revssh_chroot_dir/<acct>
#   <acct>:root 0755 $revssh_chroot_dir/<acct>/socket

our $revssh_chroot_dir = '/var/lib/satellite-revssh/';

# desired ssh-keygen binary to use
our $revssh_sshkeygen = '/usr/bin/ssh-keygen';

# tmpfs / ram-backed filesystem (NOT PERSISTENT)
# NOTE: this is actually a mtemp template.
our $revssh_tmpfsdir = '/dev/shm/satellite-revssh_XXXXXXXXXXXX';

1;

