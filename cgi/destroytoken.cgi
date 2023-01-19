#!/usr/bin/perl

# destroytoken.cgi 
# destroys the token from getlink.cgi
# this should be used after the proxying is no longer necessary
# 
# intended to be called from the host running the service to be proxied
# accepts a port number, but uses REMOTE_ADDR.

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

# and the server's IP
# (it's the host requesting this cgi)
my $srvip = $ENV{'REMOTE_ADDR'};

# check server's IP to make sure we allow it
# don't cancel a mapping from just anywhere
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
my $sth = $dbh->prepare("select alias, dsthost from proxy where alias_compare_hash = ?");
$sth->execute($nonce_hash);
my @row = $sth->fetchrow_array;

# no entry, wrong nonce, too many results
oops("Unknown nonce or nonce already destroyed") unless( $row[0] eq $nonce && ! $sth->fetchrow_array );

# must be destroyed from mapped host if mapped
oops("Nonce must be destroyed from host it was redeemed on") if ( $row[1] ne '' && defined $row[1] && $row[1] ne $srvip );

my $sth = $dbh->prepare("delete from proxy where alias = ?");
$sth->execute($nonce);
$dbh->commit;

# log for stats
syslog("info", "satellite destroy token: %s requested-from: %s", $nonce, $srvip);


print "Content-type: text/html\n\n";
print "Success! Token destroyed.\n";
