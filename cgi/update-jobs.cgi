#!/usr/bin/perl

# update-jobs.cgi
# updates the job states table
# accepts POST from a <thing> that knows about the job queue.
# format: jobstates=<job list>
#  <job list> = <jobid>\s+<state>[\n<jobid>\s+<state>...]
# curl example:
#  echo 'jobstates=' | cat - fakejobs.txt | curl --data-binary @- -XPOST https://expanse-user-content.sdsc.edu/update-jobs.cgi


use strict;
use Digest::SHA qw(sha256_base64);
use DBI;
use CGI;
use lib '../etc/';
use satconfig;
use Net::IP;

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
oops("Only POST method is supported") unless($ENV{'REQUEST_METHOD'} eq 'POST');

# get the job states
my $cgi = CGI->new;
my @args = $cgi->param;
my $jobstates = $cgi->param('jobstates');
oops("Missing 'jobstates' parameter") unless $jobstates;

# and the server's IP
# (it's the host requesting this cgi)
my $srvip = $ENV{'REMOTE_ADDR'};


# check sender's IP
# this is the check to ensure not just anyone can submit an update
# pw/authentication seems overkill here.
my $ipf = new Net::IP($satconfig::jobstateipmask);
my $ipoverlap = $ipf->overlaps(new Net::IP($srvip));
oops("Client (your) IP not in range $satconfig::jobstateipmask") unless $ipoverlap == $IP_B_IN_A_OVERLAP || $ipoverlap == $IP_IDENTICAL;


# great, update the database.
# remember not to match on the nonce directly.
# it will allow an attacker to incrementally guess
# tokens.
our $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", "", "", {
  AutoCommit => 0,
  RaiseError => 1,
});

my $now = time();

# There's a lot of churn, so if we don't delete old entries, the
# jobstates table will get huge. Delete old entries.
my $sth = $dbh->prepare("delete from jobstates where lastseen < ?");
$sth->execute($now - (3600 * 24 * 3)); # 3 days ago

# sqlite's upsert is introduced "recently", distro might not have new
# enough version. NP, we're rebuilding the entire row anyway, so 
# replace is good enough.
my $sth = $dbh->prepare("replace into jobstates (jobid,state,lastseen) values(?,?,?)");
#on conflict(jobid) do update set state = excluded.state, lastseen = excluded.lastseen");


foreach my $line (split(/\n/, $jobstates))
{
  chomp $line;
  my($job,$state) = split(/\s+/, $line);
  $job =~ s/\s//g;
  $state =~ s/\s//g;
  $job =~ s/[^-a-zA-Z0-9._]//g;
  $state =~ s/[^a-zA-Z0-0]//g;
  next unless($job);
  next unless($state);
  $sth->execute($job, $state, $now) or oops("Failed to update jobs");
}

$dbh->commit;

print "Content-type: text/html\n\n";
print "Successfully updated jobs! \n";
