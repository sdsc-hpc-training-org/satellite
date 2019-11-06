#!/usr/bin/perl

# redeemtoken.cgi 
# redeems the token from getlink.cgi
# 
# intended to be called from the host running the service to be proxied
# accepts a port number, but uses REMOTE_ADDR.

use strict;
use Digest::SHA qw(sha256_base64);
use DBI;
use CGI;
use lib '../etc/';
use satconfig;

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

# and the port
my $port = $cgi->param('port');
oops("Missing 'port' parameter") unless $port;
oops("'port' parameter isn't an integer between 1024 and 65535") unless ( $port =~ /^[0-9]{4,5}$/ && $port > 1023 && $port < 65536);

# and the server's IP
# (it's the host requesting this cgi)
my $srvip = $ENV{'REMOTE_ADDR'};

# great, update the database.
# remember not to match on the nonce directly.
# it will allow an attacker to incrementally guess
# tokens.
my $nonce_hash = sha256_base64($nonce);
our $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", "", "", {
  AutoCommit => 0,
  RaiseError => 1,
});
# but first make sure the token isn't already redeemed.
my $sth = $dbh->prepare("select alias from proxy where alias_compare_hash = ? and state = 'pending'");
$sth->execute($nonce_hash);
my @row = $sth->fetchrow_array;
oops("Unknown nonce or nonce already used") unless( $row[0] eq $nonce && ! $sth->fetchrow_array );
my $sth = $dbh->prepare("update proxy set dsthost=?, dstport=?, dstpath='/', state='mapped', modified = current_timestamp where alias_compare_hash = ?");
$sth->execute($srvip, $port, $nonce_hash);
$dbh->commit;


print "Content-type: text/html\n\n";
print "Success!\n";
