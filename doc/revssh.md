# Reverse-SSH Capability

# What? WHY?
Some environments that would otherwise be appropriate for Satellite lack technical or administrative support for the Satellite server to open a TCP socket to the reverse-proxied application.

This capability leverages the reverse-tunnel feature of SSH to bridge those restrictions, so long as the application is able to reach the Satellite server's SSH daemon.

# Theory of Operation
## High-Level
* The application runs a small shell script (*revssh client*) that will SSH to the Satellite server and use `ssh -R ...` to create a reverse tunnel.
* The reverse tunnel creates a listening UNIX domain socket on the Satellite server.
* Connections to this UNIX socket (ie from Apache httpd) result in the ssh client making an outbound connection on its end.
* Data is tunneled back to Apache and ultimately the web browser/client.

## Authenticating the Revssh Client

### Naive Approach
The naive approach uses a single account with a static password or SSH key pair as authenticators. The authenticator is communicated to the revssh client when redeeming the Satellite token.
  
This approach is troublesome because the authenticator can be used by anyone at anytime to replace a victim's Unix socket and effectively reroute their Satellite URL somewhere else.

### Iteration 2: Multiple Accounts
We can mitigate this somewhat by creating multiple accounts, and each time a Satellite token is redeemed, pick a free account, and hand out its authenticator.
  
This approach is still troublesome because a previous holder of the authenticator can still use it to hijack a victim's Satellite URL.

### Iteration 3: Rotate Authenticators
We can reset/regenerate the authenticator for an account each time it is returned to the pool. A previous holder would not be able to use their authenticator because it is no longer valid.

At this point, this approach is technically functional and addresses the above concerns. This approach, however, requires additional `sudo` privileges (or some root process, setuid program, etc.) to change the authenticator. We would like to avoid this to minimize the privileged access granted to Satellite.

### Iteration 4: SSH Certificates
Modern OpenSSH supports the use of *SSH Certificates*, which allow an *SSH CA* to issue a certificate to convey the public key instead of requiring it to be placed in some trusted location. We can leverage this by trusting an SSH CA for authenticating (only) these accounts, and allowing the web server to sign certificates.
  
The certificates come with some added controls not available in previous iterations.
* They have an expiration time, which can be helpfully set to the end of the Satellite session's maximum lifetime. The authenticator will self-invalidate if the process to reclaim the account does not run in time.
* The certificate contains a list of principals (usually one) that it may be used for. This allows the Revssh client to derive the target account unambiguously. It also allows the clean-up process to use a long-lived certificate whose only allowed capability is to kill off sshd processes owned by any account in the pool.


## Containing the Revssh Account
As the Revssh client can SSH in to the Satellite server, restrictions must be put in place to prevent that login from doing anything unwanted.

### Launch Processes On Server (Includes File Transfer)
This is prevented by using a `force-command` directive, either in `sshd_config` or in the certificate. This can also be restricted with chroot (see below).

### Tunnel Connections OUT of Server
SSHd allows restricting port-forwarding to just `remote` as opposed to any or `local` connections. We're concerned with preventing `local` tunneling, so setting to remote-only addresses this.

### Squat Another Account's Socket Path
The socket path created on the Satellite server is unfortunately client-defined. We can limit the containing directory by using SSHd's `chroot` function. No two accounts should share the same `chroot`. Note: A revssh client can create any number of sockets within their chroot, however Satellite will only attempt to use one at a predetermined location: `[chroot]/[account name]/sockets/remote`.

### Create Listening (TCP) Port on Server
This is actually something we'll have to accept unless specific invocations of `listen()` (tcp, and not UNIX domain) are blocked through some other means like seccomp. The utility of this capability can be limited by firewall rules and impact reduced to denial-of-service caused by port exhaustion.

### Long-Lived Connection
Once the Satellite session has expired or been deleted, an existing login may continue to persist unless it is killed off. Furthermore, a certificate will still be valid until it has expired.
  
We employ a KRL to prematurely invalidate certificates for deleted Satellite sessions. This way a revssh client can continue to try reconnecting, however it will not succeed.

A cron-driven process will need to kill off any processes owned by accounts associated with deleted sessions. (Or conversely, kill off any processes owned by accounts not associated with an active session.) This can leverage a special certificate that allows the holder of the private key to authenticate as any user in the account pool, and execute only one command - to clean up the account's processes. Alternatively this might be an exception and allow the use of sudo to kill a pid.

### Point A Tunnel Somewhere Outside the Environment
This isn't really a thing that can happen on the Satellite server, but worth mentioning. A revssh client can set the target of a remote-forward to a host outside the environment and bounce the connection somewhere else.
  
This is an accepted risk and nothing new. There's nothing to prevent this from happening without reverse-ssh, so it's not a new risk. (see: user-space port redirection via socat, ncat, stunnel, redir, etc)



