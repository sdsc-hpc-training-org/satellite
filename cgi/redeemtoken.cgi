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
use Cwd;
use File::Basename qw(dirname);
use lib(dirname(Cwd::abs_path($0)) . '/../etc');
use satconfig;
use Net::IP;
use Sys::Syslog qw(:DEFAULT setlogsock);

# for revproxy; we need to invoke ssh-keygen
use File::Temp ();
File::Temp->safe_level(File::Temp::HIGH);

my $dbfile = $satconfig::dbfile;
my $ssh_keygen = $satconfig::revssh_sshkeygen;
my $tmpfsdir = $satconfig::revssh_tmpfsdir;
my $poolgroup = $satconfig::revssh_group;

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

# find out if the client wants to use revssh instead
my $revssh = $cgi->param('revssh');

# and the port
my $port = $cgi->param('port');

# revssh and port are mutually exclusive, but one needs to be used.
oops("'port' and 'revssh' are mutually exclusive") if ( $revssh && $port );
oops("Missing 'port' parameter, or try 'revssh=1' instead") unless ( $port || $revssh );

# check validity of port if not doing revssh
if ( ! $revssh )
{
    oops("'port' parameter isn't an integer between 1024 and 65535") unless ( $port =~ /^[0-9]{4,5}$/ && $port > 1023 && $port < 65536);
}

# and the server's IP
# (it's the host requesting this cgi)
my $srvip = $ENV{'REMOTE_ADDR'};

# check server's IP to make sure we allow it
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

# but first make sure the token isn't already redeemed.
my $sth = $dbh->prepare("select alias from proxy where alias_compare_hash = ? and state = 'pending'");
$sth->execute($nonce_hash);
my @row = $sth->fetchrow_array;
oops("Unknown nonce or nonce already used") unless( $row[0] eq $nonce && ! $sth->fetchrow_array );

# before updating the database, revssh requires something different: a pubkey in the database and
# a private key to the client.
# an appropriate account must also be selected.
if ( $revssh )
{
    eval
    {
        # create a temp dir and generate an ssh key pair
        my $tmpdir = File::Temp->newdir($tmpfsdir);
        my $keydir = $tmpdir->dirname;
        my @keygen_args = ( '-N', '', '-t', 'ed25519', '-f', "$keydir/tempkey", '-q', '-C', '' );
        my $res = system($ssh_keygen, @keygen_args);
        die("unable to generate ssh key pair with $ssh_keygen") if ( $res != 0 );

        # read public key
        my $pubkey = '';
        {
            local $/;
            open(my $fh, '<', "$keydir/tempkey.pub") or die("$keydir/tempkey.pub: $!");
            $pubkey = <$fh>;
            close($fh);
        }
        chomp($pubkey);

        # read private key
        my $privkey = '';
        {
            local $/;
            open(my $fh, '<', "$keydir/tempkey") or die("$keydir/tempkey: $!");
            $privkey = <$fh>;
            close($fh);
        }

        # pick a username
        # brute-force by trying to cram an entry into the db until it succeeds
        my @grent = getgrnam($poolgroup);
        die("revssh_group $poolgroup does not exist, cannot use revssh") unless ( @grent );
        my @pool = split('\s+', $grent[3]);
        die("revssh_group $poolgroup appears to be empty, cannot use revssh") unless ( scalar @pool > 1 );
        while ( my $acct = shift(@pool) )
        {
            my $sth = $dbh->prepare("update proxy set dsthost=?, revssh_user=?, revssh_pubkey=?, dstpath='/', state='mapped', modified = current_timestamp where alias_compare_hash = ?");
            eval
            {
                local $sth->{PrintError}; # don't print errors here, it's probably okay.
                $sth->execute($srvip, $acct, $pubkey, $nonce_hash);
            };
            if ( $@ )
            {
                if ( $@ =~ /unique constraint failed/i )
                {
                    $dbh->rollback;
                }
                else
                {
                    die($@);
                }
            }
            else
            {
                $dbh->commit;
                syslog("info", "satellite redeemed token %s mapped-to: revssh:%s from=%s %s", $nonce, $acct, $srvip, $pubkey);
                print "Content-type: text/plain\n\n";
                print "Success!\n";
                print "$acct\n";
                print "$privkey";
                exit;
            }
            # still here? try again.
            $dbh->rollback;
        }

        # still here? give up.
        die("tried to create revssh proxy entry with all accounts in revssh_group $poolgroup, did not succeed with any");
    };
    if ( $@ )
    {
        syslog('warning', "satellite error revssh: %s", $@);
        oops("Unable to create revssh proxy entry. More details in host's syslog.");
    }
}

else
{
    my $sth = $dbh->prepare("update proxy set dsthost=?, dstport=?, dstpath='/', state='mapped', modified = current_timestamp where alias_compare_hash = ?");
    $sth->execute($srvip, $port, $nonce_hash);
    $dbh->commit;

    # log for stats
    syslog("info", "satellite redeemed token: %s mapped-to: %s:%d", $nonce, $srvip, $port);
    print "Content-type: text/html\n\n";
    print "Success!\n";
    exit;
}


