#!/usr/bin/perl -w
# generates a proxy token
use strict;
use Digest::SHA qw(sha256_base64);
use DBI;
use Cwd;
use File::Basename qw(dirname);
use lib(dirname(Cwd::abs_path($0)) . '/../etc');
use satconfig;
use Net::IP;
use Sys::Syslog qw(:DEFAULT setlogsock);


sub oops($)
{
  my $msg = shift;
  print "Content-type: text/plain\n\n";
  printf "Oops! %s\n", $msg;
  $main::dbh->rollback if defined $main::dbh;
  exit;
}

# stop and check remote IP here. Don't issue tokens to just anyone.
my $srvip = $ENV{'REMOTE_ADDR'};
my $ipf = new Net::IP($satconfig::tgtipmask);
oops("Client (your) IP not in range $satconfig::tgtipmask, please try from within the cluster.") unless $ipf->overlaps(new Net::IP($srvip)) == $IP_B_IN_A_OVERLAP;

# database lives here
# CREATE TABLE proxy ( alias text not null, alias_compare_hash text not null, modified timestamp default current_timestamp, dsthost text, dstport integer, dstpath text, state text not null);
my $dbfile = $satconfig::dbfile;

# well, we can't assume there's a usable random library, so let's use
# /dev/urandom. 16 bytes (128 bits) should be enough.
#my $nonce = unpack("h*", `dd if=/dev/urandom bs=1 count=16 2>/dev/null`);

# actually, random hex chars is pretty unfriendly.
# let's try some random words instead.
my @noncelist;
my $tries = 0;
do
{
    my $tword = lc(`shuf --random-source=/dev/urandom -n 1 ../var/words`);
    chomp $tword;
    if ( $tword =~ /^[a-z0-9]+$/ )
    {
        unshift(@noncelist, $tword);
    }
    $tries++;
    if ( $tries > 1000 )
    {
        oops("Problem generating unique URL. Sorry!");
        exit;
    }
} while ( scalar @noncelist < 3 );
my $nonce = join('-', @noncelist);

# we calc a hash since this is the thing we use to dig out
# the record later. don't compare on alias since it allows an
# attacker to incrementally guess valid aliases based on response time.
my $nonce_hash = sha256_base64($nonce);


# stick it in the DB for future use.
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", "", "", {
  AutoCommit => 0,
  RaiseError => 1,
});
my $sth = $dbh->prepare("insert into proxy (alias, alias_compare_hash, state) values(?, ?, 'pending')");
$sth->execute($nonce, $nonce_hash);
$dbh->commit;

# log this event to syslog so we can review it later
# note: the token isn't a huge secret, hopefully the underlying webapp
# has some kind of authentication.
syslog("info", "satellite issued token: %s requested-from: %s", $nonce, $srvip);

print "Content-type: text/plain\n\n";
print "Your token is \n$nonce\n";
