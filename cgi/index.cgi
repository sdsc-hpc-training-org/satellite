#!/usr/bin/perl

# index.cgi 
# displays info if a URL is waiting or taken or whatever.
#
# retrieves the requested site from $ENV{'HTTP_HOST'}


use strict;
use Digest::SHA qw(sha256_base64);
use DBI;
use CGI;
use lib '../etc/';
use satconfig;
use Net::IP;

use Data::Dumper;
my $dbfile = $satconfig::dbfile;
my $domain = $satconfig::extbasename;

sub oops($)
{
  my $msg = shift;
  print "Content-type: text/plain\n\n";
  printf "Oops! %s\n", $msg;
  $main::dbh->rollback if defined $main::dbh;
  exit;
}

sub default_message
{
  print "Content-type: text/plain\n\n";
  print "Please see documentation on how to use this service.\n";
  exit;
}

sub pending_message
{
  print "Content-type: text/plain\n\n";
  print "This token is pending redemption.\n";
  print "Please make a GET request from the host running the service to proxy.\n";
  print "\nExample: curl 'https://manage.comet-user-content.sdsc.edu/redeemtoken.cgi?token=<token>&port=<service_port>'\n";
  exit;
}

sub mapping_message
{
  print "Content-type: text/plain\n\n";
  print "This token is mapped but waiting on an internal process.\n";
  print "Please be patient. This will take a couple of minutes!\n";
  exit;
}

# stop if wrong method
oops("Only GET method is supported") unless($ENV{'REQUEST_METHOD'} eq 'GET');

# get the alias
my $fullhost = $ENV{'HTTP_HOST'};
my ($nonce,$remainderhost) = split(/\./, $fullhost, 2);

# junk = default
if ( lc($remainderhost) ne lc($domain) )
{
  default_message();
}
if ( $nonce =~ /[^-a-zA-Z0-9]/ )
{
  default_message();
}

# normalize case because dns names are not case sensitive
$nonce = lc($nonce);

# maybe the alias is pending, meaning the user needs to redeem the token.
my $nonce_hash = sha256_base64($nonce);
our $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", "", "", {
  AutoCommit => 0,
  RaiseError => 1,
});
my $sth = $dbh->prepare("select alias from proxy where alias_compare_hash = ? and state = 'pending'");
$sth->execute($nonce_hash);
my @row = $sth->fetchrow_array;
if ( $row[0] eq $nonce )
{
  pending_message();
}

# okay, how about waiting on cron?
$sth = $dbh->prepare("select alias from proxy where alias_compare_hash = ? and state = 'mapped'");
$sth->execute($nonce_hash);
my @row = $sth->fetchrow_array;
if ( $row[0] eq $nonce )
{
  mapping_message();
}

# whatever.
default_message();
