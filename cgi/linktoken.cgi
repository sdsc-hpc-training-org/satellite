#!/usr/bin/perl

# linktoken.cgi 
# links token with a job id
# this should be used after getting a token, once you know the job id
# linking the token isn't required, but does help provide job state to the
# pending page.

use strict;
use Digest::SHA qw(sha256_base64);
use DBI;
use CGI;
use Cwd;
use File::Basename qw(dirname);
use lib(dirname(Cwd::abs_path($0)) . '/../etc');
use satconfig;
use Net::IP;
use Sys::Syslog qw(:DEFAULT setlogsock);


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

# and the job id
my $jobid = $cgi->param('jobid');
# remove junk from jobid
# this should agree with update_jobs.cgi
$jobid =~ s/\s//g;
$jobid =~ s/[^-a-zA-Z0-9._]//g;
# jobid shouldn't be TOO long, else syslog message gets truncated.
oops("Missing 'jobid' parameter") unless $jobid && $jobid ne '' && length $jobid < 48;

# check server's IP to make sure we allow it
my $srvip = $ENV{'REMOTE_ADDR'};
my $ipmatch = 0;
foreach my $ipmask ( split(/\s+/, $satconfig::tgtipmask) )
{
    my $ipf = new Net::IP($ipmask);
    my $ipoverlap = $ipf->overlaps(new Net::IP($srvip));
    if ( $ipoverlap == $IP_B_IN_A_OVERLAP || $ipoverlap == $IP_IDENTICAL )
    {
        $ipmatch = 1;
        last;
    }
}
oops("Client (your) IP not in ranges $satconfig::tgtipmask, please try from within the cluster.") unless ( $ipmatch == 1 );

# great, update the database.
# remember not to match on the nonce directly.
# it will allow an attacker to incrementally guess
# tokens.
my $nonce_hash = sha256_base64($nonce);
our $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", "", "", {
  AutoCommit => 0,
  RaiseError => 1,
});

# whatever the token is we're going to delete its entry
# we do want to make sure the token exists
my $sth = $dbh->prepare("select alias, jobid from proxy where alias_compare_hash = ?");
$sth->execute($nonce_hash);
my @row = $sth->fetchrow_array;

# no entry, wrong nonce, too many results
oops("Unknown nonce or nonce already destroyed") unless( $row[0] eq $nonce && ! $sth->fetchrow_array );

# don't allow changing the linking
oops("Nonce already linked to a jobid, you can do this only once!") if ( $row[1] ne '' && defined $row[1] );

my $sth = $dbh->prepare("update proxy set jobid = ? where alias = ?");
$sth->execute($jobid, $nonce);
$dbh->commit;

# log for stats
syslog("info", "satellite link token: %s->%s requested-from: %s", $nonce, $jobid, $srvip);


print "Content-type: text/html\n\n";
print "Success! Token linked to jobid.\n";
