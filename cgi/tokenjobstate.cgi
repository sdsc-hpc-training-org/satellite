#!/usr/bin/perl

# tokenjobstate.cgi 
# retrieves job state for given token
# this should be used after linking the job id
# linking is optional and just provides data to improve user experience
# if not linked this script returns an empty string, so it's safe to
# use this script by default.
#
# when linked, output is a single line:
# <staleness in secs> <state>
#
# state is either a basic state or extended state.
#
# basic: 
#  U  = Unknown
#  PE = Pending (waiting for token to be redeemed)
#  M  = Mapped (mapping entry created, cron not run yet)
#  PR = Proxied (cron created proxy entry) user agent should reload url.
#
# extended (includes basic, plus):
#  Q  = Job in the batch queue.
#  R  = Job running, but hasn't redeemed token yet.
#  D  = Job died, will never run.

use strict;
use Digest::SHA qw(sha256_base64);
use DBI;
use CGI;
use lib '../etc/';
use satconfig;
use Net::IP;
use Sys::Syslog qw(:DEFAULT setlogsock);

use Data::Dumper;

my $dbfile = $satconfig::dbfile;

sub oops($)
{
  my $msg = shift;
  print "Content-type: text/plain\n\n";
  printf "Oops! %s\n", $msg;
  $main::dbh->rollback if defined $main::dbh;
  exit;
}

# stop if wrong method
oops("Only GET method is supported") unless($ENV{'REQUEST_METHOD'} eq 'GET');

# get the token/nonce
my $cgi = CGI->new;
my $nonce = $cgi->param('token');
oops("Missing 'token' parameter") unless $nonce;

# token/nonce can be the hostname part of a URL
# yank the token from the hostname, should be leftmost component.
if ( $nonce =~ /\./ )
{
    my @parts = split(/\./, $nonce);
    $nonce = $parts[0];
    oops("Missing 'token' parameter") unless $nonce;
}

# requests come from the user's browser, which can be anywhere.
# don't restrict.

# great, query the database.
# remember not to match on the nonce directly.
# it will allow an attacker to incrementally guess
# tokens.
my $nonce_hash = sha256_base64($nonce);
our $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", "", "", {
  AutoCommit => 0,
  RaiseError => 1,
});

my $sth = $dbh->prepare("select ps.alias, js.state, strftime('%s',js.lastseen), ps.state, strftime('%s',ps.modified), ps.jobid from proxy ps left join jobstates js using (jobid) where ps.alias_compare_hash = ?");
$sth->execute($nonce_hash);
my @row = $sth->fetchrow_array;

# we're going to return something at this point, and it can't be an error.
print "Content-type: text/plain\n\n";

if ( $row[0] eq $nonce && ! $sth->fetchrow_array ) 
{
    # job state needs to be scrubbed
    # last line of defense for XSS
    my $jobstate = '';
    $jobstate = $row[1] if ( defined $row[1] );
    $jobstate =~ s/[^-A-Za-z0-9 ._]//g;

    # also propagate staleness since we want to know when the entry was 
    # last updated
    my $lastseen = 0;
    $lastseen = $row[2] if ( defined $row[2] );
    my $staleness = time() - $lastseen;

    # we're going to return a synthetic state based on more info
    my $dispjobstate = 'U';

    my $proxystate = '';
    $proxystate = $row[3] if ( defined $row[3] );
    $proxystate =~ s/[^-A-Za-z0-9 ._]//g;

    my $proxylastseen = 0;
    $proxylastseen = $row[4] if ( defined $row[4] );
    my $proxystaleness = time() - $proxylastseen;

    my $jobid  = '';
    $jobid = $row[5] if ( defined $row[5] );

    # convert jobstate into Waiting/Running/Gone/Unknown
    # this is for slurm, other resource managers need something else.
    if ( grep(/^$jobstate$/, @satconfig::JOB_GONE_STATE_CODES) )
    {
        $jobstate = 'G';
    } 
    elsif ( grep(/^$jobstate$/, @satconfig::JOB_RUN_STATE_CODES) )
    {
        $jobstate = 'R';
    } 
    elsif ( grep(/^$jobstate$/, @satconfig::JOB_WAIT_STATE_CODES) )
    {
        $jobstate = 'W';
    } 
    else
    {
        $jobstate = 'U';
    }

    # the lack of a job id or job state  means we can't use extended states
    # just use the proxy states
    # also ignore job state if it is too old (10m / 600s)
    if ( $jobid eq '' || ( $jobid ne '' && $jobstate eq 'U') || $staleness > 600 )
    {
        if ( $proxystate eq 'pending' )
        {
            $dispjobstate = 'PE';
        } 
        elsif ( $proxystate  eq 'mapped' )
        {
            $dispjobstate = 'M';
        } 
        elsif ( $proxystate eq 'proxied' )
        {
            $dispjobstate = 'PR';
        }
    } 
    
    # use extended states since we have a jobid
    else
    {
        # the job is waiting
        if ( $jobstate eq 'W' )
        {
            # waiting and not mapped means it's in the queue
            if ( $proxystate eq 'pending' )
            {
                $dispjobstate = 'Q';
            } 
            # job redeemed token before the job state updated
            elsif ( $proxystate eq 'mapped' )
            {
                $dispjobstate = 'M';
            }
            # job redeemed token and proxy entry created before job state updated
            elsif ( $proxystate eq 'proxied' )
            {
                $dispjobstate = 'PR';
            }
        }

        # the job is running
        elsif ( $jobstate eq 'R' )
        {
            # job is running but hasn't redeemed token yet.
            if ( $proxystate eq 'pending' )
            {
                $dispjobstate = 'R';
            } 
            # job is running, redeemed token, cron not yet run.
            elsif ( $proxystate eq 'mapped' )
            {
                $dispjobstate = 'M';
            } 
            # job running, redeemed token, cron run.
            elsif ( $proxystate eq 'proxied' )
            {
                $dispjobstate = 'PR';
            }
        }  
        # the job disappeared; it may have been cancelled or ran and exited
        elsif ( $jobstate eq 'G' )
        {
            # it's never coming back, so always dead.
            $dispjobstate = 'D';
        } 
    }

    printf("%d %s", $proxystaleness, $dispjobstate);
}

