#!/usr/bin/perl

# tokenjobstate.cgi 
# retrieves job state for given token
# this should be used after linking the job id
# linking is optional and just provides data to improve user experience
# if not linked this script doesn't return an error, so it's safe to
# use this script by default.

use strict;
use Digest::SHA qw(sha256_base64);
use DBI;
use CGI;
use lib '../etc/';
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

# whatever the token is we're going to delete its entry
# we do want to make sure the token exists
my $sth = $dbh->prepare("select ps.alias, js.state from jobstates js left join proxy ps using (jobid) where ps.alias_compare_hash = ?");
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

    printf("%s", $jobstate);
}


