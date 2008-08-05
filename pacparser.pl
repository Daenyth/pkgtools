#!/usr/bin/perl

use strict;
#use warnings;
#use feature ':5.10';

use Data::Dumper;
# pacman.conf parsing code modified from "powerpill" by Xyne, licensed under the GPL2
# powerpill is available at http://aur.archlinux.org/packages.php?ID=18882
my %paths;
my $mirrors = {};
my $PASSIVE_FTP;
my $SHOW_FILE_SIZES;

my $DEFAULT_CONF     = '/etc/pacman.conf';
my $DEFAULT_CACHE    = '/var/cache/pacman/pkg/';
my $DEFAULT_DATABASE = '/var/lib/pacman/';

sub parsePacConfig
{
	my $file = shift;
	my $repo = shift;
	# each depth of recursion will add itself to the list before going deeper
	# so that it's possible to detect reciprocal Includes
	my @parents = @_;
	open (my $fh, '<', $file) or die "Unable to open $file: $!\n";
	while ( defined(my $line = <$fh>) )
	{
		next if ($line =~ /^ *#/); # Skip comments
		next if ($line =~ /^ *$/); # Skip empty lines

#		if ($line =~ m/^\s*RootDir\s*=\s*(.+)\s*$/)
#		{
#			my $dir = $1;
#			if ( substr($dir,-1) ne '/' )
#			{
#				$dir .= '/';
#			}
#			$paths{'RootDir'} = $dir;
#		}
#		elsif ($line =~ m/^\s*DBPath\s*=\s*(.+)\s*$/)
#		{
#			my $dir = $1;
#			if ( substr($dir,-1) ne '/' )
#			{
#				$dir .= '/';
#			}
#			$paths{'DBPath'} = $dir;
#		}
#		elsif ($line =~ m/^\s*CacheDir\s*=\s*(.+)\s*$/)
#		{
#			my $dir = $1;
#			if ( substr($dir,-1) ne '/' )
#			{
#				$dir .= '/';
#			}
#			push @{ $paths{'CacheDir'} }, $dir;
#		}
		if ($line =~ m/^\s*NoPassiveFtp\s*$/)
		{
			$PASSIVE_FTP = 'no';
		}
#		elsif ($line =~ m/^\s*ShowSize\s*$/)
#		{
#			$SHOW_FILE_SIZES = 'yes';
#		}
		elsif ($line =~ m/^\s*\[\s*(.*?)\s*\]\s*$/)
		{
			$repo = $1;
		}
		elsif ($line =~ m/^\s*Server\s*=\s*(.+)\s*$/ and $repo)
		{
			my $server = $1;
			# add the server to the list (preserving order, but ignoring duplicates)
			push (@{ $mirrors->{$repo} }, $server) if not grep {$server eq $_} @{ $mirrors->{$repo} };
		}
		# only descent into configs that we haven't been in before
		elsif ($line =~ m/^\s*Include\s*=\s*(.+)\s*$/)
		{
			# check that the Include file is not a parent of this recursion
			if (!grep {$_ eq $1} @parents)
			{
				&parsePacConfig($1, $repo, @parents, $file);
			}
		}
	}
	close $fh;
}
parsePacConfig( "$DEFAULT_CONF" );
print Dumper( $mirrors );
