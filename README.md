GetTor Revamp
=============

GetTor Revamp done during the Google Summer of Code 2014 for the Tor Project.
This repository continues to being used for improvements and further
development.

What is GetTor?
===============

GetTor was created as a program for serving Tor and related files over SMTP,
thus avoiding direct and indirect _censorship_ of Tor's software, in particular,
the Tor Browser Bundle (TBB). Users interacted with GetTor by sending emails
to a specific email address. After the user specified his OS and language,
GetTor would send him an email with an attachment containing the requested
package. This worked well for a while, but the bundles started to get too
large for being sent as attachments in most email providers. In order to fix
this, GetTor started to send (Dropbox) links instead of attachments.

What are the goals of the new GetTor?
=====================================

Here is a list of the main goals the new GetTor should accomplish:

 * Safe. Remember we are serving people under _heavy censorship_.
 * Easy to use. The fewer user interactions, the better.
 * Clean code. It should be clear to other developers/contributors how GetTor
 works and how it can be improved.
 * Automated. We should try to automate things as much as possible.
 * Language and provider friendly. It should be easy to support new languages
 and to add new providers for storing packages and generate links.

Installing GetTor
=================

To install gettor locally please install the following packages (on debian):

python3-coverage
python3-dkim
python3-dns
python3-internetarchive
python3-openssl
python3-pytest
python3-requests-oauthlib
python3-service-identity
python3-twisted
sqlite3

The following packages are needed to run a gettor instance:

internetarchive
jq
rclone

Specifically:
internetarchive is needed to send Tor Browser files via command line to the internet archive.
jq is a json parser that is used to find out about the new tor browser releases.
Both internetarchive and jq are used in: scripts/update_files

The following packages are instead needed to deploy gettor via ansible:

ansible
ansible-lint

Gettor ansible playbooks live at: https://gitweb.torproject.org/admin/services/gettor.git/

Finally the following package is used store Tor Browser files via git and support large files:
git-lfs



Once gettor is installed you can run it with:

```
$ ./bin/gettor_service start
```

Running tests
=================

GetTor includes PyTest unit tests. To run the tests, first install some dependencies:


```
$ pytest-3 tests/
```
