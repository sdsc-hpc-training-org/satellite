#!/usr/bin/perl -w
# generates a proxy token
use strict;
use DBI;


print "Content-type: text/plain\n\n";

my $host = `hostname -f`;
print "Running on $host";

# database lives here
# CREATE TABLE proxy ( alias text not null, created timestamp default current_timestamp, dsthost text, dstport integer, dstpath text);
my $dbfile = "./state.sqlite";

# well, we can't assume there's a usable random library, so let's use
# /dev/urandom. 16 bytes (128 bits) should be enough.
#my $nonce = unpack("h*", `dd if=/dev/urandom bs=1 count=16 2>/dev/null`);

# actually, random hex chars is pretty unfriendly.
# let's try some random words instead.
my @noncelist;
my $tries = 0;
do
{
    my $tword = lc(`shuf --random-source=/dev/urandom -n 1 words`);
    chomp $tword;
    if ( $tword =~ /^[a-z0-9]+$/ )
    {
        unshift(@noncelist, $tword);
    }
    $tries++;
    if ( $tries > 1000 )
    {
        print "Problem generating unique URL. Sorry!\n";
        exit;
    }
} while ( scalar @noncelist < 3 );
my $nonce = join('_', @noncelist);


# stick it in the DB for future use.
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", "", "", {
  AutoCommit => 0,
  RaiseError => 1,
});
my $sth = $dbh->prepare("insert into proxy (alias) values(?)");
$sth->execute($nonce);
$dbh->commit;



print "Your token is $nonce";
