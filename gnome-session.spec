%define glib2_version 2.2.0
%define pango_version 1.2.0
%define gtk2_version 2.2.0
%define libgnome_version 2.3.0
%define libgnomeui_version 2.3.0
%define gnome_vfs2_version 2.3.0
%define gconf2_version 2.2.0
%define gnome_desktop_version 2.2.0
%define dbus_glib_version 0.70
%define dbus_version 0.90

%define po_package gnome-session-2.0

Summary: GNOME session manager
Name: gnome-session
Version: 2.16.0
Release: 4%{?dist}
URL: http://www.gnome.org
Source0: %{name}-%{version}.tar.bz2
Source1: redhat-default-session
Source2: gnome.desktop
License: GPL 
Group: User Interface/Desktops
BuildRoot: %{_tmppath}/%{name}-root

Requires: redhat-artwork >= 0.20
Requires: system-logos
# required to get gconf-sanity-check-2 in the right place
Requires: GConf2 >= %{gconf2_version}
# Needed for gnome-settings-daemon
Requires: control-center

%ifnarch s390 s390x
Requires: gnome-volume-manager
%endif

## we conflict with gdm that contains the GNOME gdm xsession
Conflicts: gdm < 1:2.6.0.8-5

Patch1: gnome-session-2.2.2-icons.patch
Patch2: gnome-session-2.0.5-login.patch
Patch3: gnome-session-2.0.5-dithering.patch

## http://bugzilla.gnome.org/show_bug.cgi?id=106450
Patch6: gnome-session-2.9.4-gnome-common.patch

# Launch gnome-user-share on login if enabled
Patch7: gnome-session-2.13.92-user-share.patch

# do shaped window for splash screen
Patch8: gnome-session-2.16.0-shaped.patch

# too much crashing
Patch9: gnome-session-2.13.4-no-crashes.patch

# http://bugzilla.gnome.org/show_bug.cgi?id=333670
Patch12: gnome-session-2.15.91-desensitize-invalid-buttons.patch

# http://bugzilla.gnome.org/show_bug.cgi?id=350848
Patch13: gnome-session-2.15.91-window-manager.patch

# http://bugzilla.gnome.org/show_bug.cgi?id=84315
Patch14: gnome-session-2.15.91-http-proxy.patch

BuildRequires: glib2-devel >= %{glib2_version}
BuildRequires: pango-devel >= %{pango_version}
BuildRequires: gtk2-devel >= %{gtk2_version}
BuildRequires: libgnome-devel >= %{libgnome_version}
BuildRequires: libgnomeui-devel >= %{libgnomeui_version}
BuildRequires: gnome-vfs2-devel >= %{gnome_vfs2_version}
BuildRequires: gnome-desktop-devel >= %{gnome_desktop_version}
BuildRequires: dbus-devel >= %{dbus_version}
BuildRequires: dbus-glib-devel >= %{dbus_glib_version}
BuildRequires: libnotify-devel
BuildRequires: control-center-devel
BuildRequires: desktop-file-utils

# this is so the configure checks find /usr/bin/halt etc.
BuildRequires: usermode

BuildRequires: intltool, autoconf, automake
BuildRequires: libtool
BuildRequires: gettext
BuildRequires: libX11-devel libXt-devel
BuildRequires: libXrandr-devel

Requires(pre): GConf2 >= 2.14
Requires(post): GConf2 >= 2.14
Requires(preun): GConf2 >= 2.14

%description

gnome-session manages a GNOME desktop session. It starts up the other core 
GNOME components and handles logout and saving the session.

%prep
%setup -q

%patch1 -p1 -b .icons
%patch2 -p1 -b .login
%patch3 -p1 -b .dithering
%patch6 -p1 -b .gnome-common
%patch7 -p1 -b .user-share
%patch8 -p1 -b .shaped
%patch9 -p1 -b .no-crashes
%patch12 -p1 -b .desensitize-invalid-buttons
%patch13 -p1 -b .window-manager
%patch14 -p1 -b .http-proxy

%build

#workaround broken perl-XML-Parser on 64bit arches
export PERL5LIB=/usr/lib64/perl5/vendor_perl/5.8.2 perl

aclocal
automake
intltoolize --force
autoheader
autoconf

%configure --with-halt-command=/usr/bin/poweroff --with-reboot-command=/usr/bin/reboot
make

%install
rm -rf $RPM_BUILD_ROOT

export GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL=1
make install DESTDIR=$RPM_BUILD_ROOT
unset GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL

desktop-file-install --vendor gnome --delete-original                   \
  --dir $RPM_BUILD_ROOT%{_datadir}/applications			        \
  --add-only-show-in GNOME                                              \
  --add-category Settings                                               \
  --add-category AdvancedSettings                                       \
  $RPM_BUILD_ROOT%{_datadir}/applications/*

./mkinstalldirs ${RPM_BUILD_ROOT}%{_datadir}/xsessions/
install -m 755 %{SOURCE2} ${RPM_BUILD_ROOT}%{_datadir}/xsessions/

/bin/rm -f $RPM_BUILD_ROOT%{_datadir}/gnome/default.session

# Bad evilness to remove gnome-volume-manager dependency on s390
%ifarch s390 s390x
sed -i -e 's/num_clients=7/num_clients=6/' -e '/^6,.*$/d' %{SOURCE1}
%endif

install -m 644 %{SOURCE1} $RPM_BUILD_ROOT%{_datadir}/gnome/default.session

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/xdg/autostart
mkdir -p $RPM_BUILD_ROOT%{_datadir}/gnome/autostart

#/bin/rm -r $RPM_BUILD_ROOT/var/scrollkeeper

## remove splash screen
rm -r $RPM_BUILD_ROOT%{_datadir}/pixmaps/splash

%find_lang %{po_package}

%clean
rm -rf $RPM_BUILD_ROOT

%post
export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
gconftool-2 --makefile-install-rule %{_sysconfdir}/gconf/schemas/gnome-session.schemas > /dev/null || :
/sbin/ldconfig

%pre
if [ "$1" -gt 1 ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/gnome-session.schemas > /dev/null || :
fi

%preun
if [ "$1" -eq 0 ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/gnome-session.schemas > /dev/null || :
fi

%postun
/sbin/ldconfig

%files -f %{po_package}.lang
%defattr(-,root,root)

%doc AUTHORS COPYING ChangeLog NEWS README

%{_datadir}/gnome
%{_datadir}/applications
%{_datadir}/xsessions/*
%{_datadir}/man/man*/*
%{_bindir}/*
%{_sysconfdir}/gconf/schemas/*.schemas
%{_sysconfdir}/xdg/autostart
%{_datadir}/gnome/autostart

%changelog
* Wed Oct 18 2006 Matthias Clasen <mclasen@redhat.com> - 2.16.0-4
- Fix scripts according to the packaging guidelines

* Thu Sep  7 2006 Matthias Clasen <mclasen@redhat.com> - 2.16.0-3.fc6
- Fix position of icons in the splash screen  (#205508)

* Wed Sep  6 2006 Ray Strode <rstrode@redhat.com> - 2.16.0-2.fc6
- set http_proxy environment variable from GNOME settings 
  (bug 190041)

* Mon Sep  4 2006 Matthias Clasen <mclasen@redhat.com> - 2.16.0-1.fc6
- Update to 2.16.0

* Mon Aug 21 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.92-1.fc6
- Update to 2.15.92
- Add %%preun and %%postun scripts

* Mon Aug 14 2006 Ray Strode <rstrode@redhat.com> - 2.15.91-1.fc6
- Update to 2.15.91

* Sun Aug 13 2006 Ray Strode <rstrode@redhat.com> - 2.15.90-4.fc6
- fix window manager launching script. Patch from 
  Tim Vismor <tvismor@acm.org> (bug 202312)

* Fri Aug 11 2006 Ray Strode <rstrode@redhat.com> - 2.15.90-3.fc6
- start gnome-window-decorator and pass "gconf" when invoking
  compiz

* Thu Aug 10 2006 Ray Strode <rstrode@redhat.com> - 2.15.90-2.fc6
- update patch from 2.15.4-3 to be more session friendly (bug 201473)

* Fri Aug  4 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.90-1.fc6
- Update to 2.15.90

* Thu Aug  3 2006 Soren Sandmann <sandmann@redhat.com> - 2.15.4-3
- Add patch to (a) add configuration option for window manager, (b) start the window
  manager, and (c) disable splash screen by default.

* Wed Jul 19 2006 John (J5) Palmieri <johnp@redhat.com> - 2.15.4-2
- Add BR for dbus-glib-devel

* Thu Jul 13 2006 Ray Strode <rstrode@redhat.com> - 2.15.4-1
- Update to 2.15.4

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 2.15.1-5.1
- rebuild

* Mon Jun 12 2006 Bill Nottingham  <notting@redhat.com> 2.15.1-5
- remove obsolete automake14 buildreq

* Fri Jun  9 2006 Matthias Clasen  <mclasen@redhat.com> 2.15.1-4
- Add more missing BuildRequires

* Tue Jun  6 2006 Matthias Clasen  <mclasen@redhat.com> 2.15.1-3
- Add BuildRequires: intltool, autoconf, automake 

* Mon Jun  5 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.1-2
- Require system-logos, not fedora-logos

* Wed May 10 2006 Matthias Clasen <mclasen@redhat.com> - 2.15.1-1
- Update to 2.15.1

* Mon Apr 10 2006 Matthias Clasen <mclasen@redhat.com> - 2.14.1-2
- Update to 2.14.1

* Mon Mar 13 2006 Matthias Clasen <mclasen@redhat.com> - 2.14.0-1
- Update to 2.14.0

* Thu Mar 09 2006 Ray Strode <rstrode@redhat.com> - 2.13.92-5
- fix up path creation functions 

* Thu Mar 09 2006 Ray Strode <rstrode@redhat.com> - 2.13.92-4
- create ~/.config/autostart before trying to migrate
  session-manual to it (bug 179602).

* Mon Mar 06 2006 Ray Strode <rstrode@redhat.com> - 2.13.92-3
- Patch from Vincent Untz to fix session editing (upstream bug 333641)
- Desensitize buttons for operations that the user isn't allowed
  to do (bug 179479).

* Wed Mar 01 2006 Karsten Hopp <karsten@redhat.de> 2.13.92-2
- BuildRequires: gnome-desktop-devel, libX11-devel, libXt-devel

* Tue Feb 28 2006 Ray Strode <rstrode@redhat.com> - 2.13.92-1
- Update to 2.13.92
- Add patch from CVS HEAD to maintain compatibility with
  version 2.13.91

* Thu Feb 23 2006 Ray Strode <rstrode@redhat.com> - 2.13.91-2
- take ownership of autostart dir (bug 182335)

* Mon Feb 13 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.91-1
- Update to 2.13.91

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 2.13.90-1.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 2.13.90-1.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Sat Jan 28 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.90-1
- Update to 2.13.90

* Tue Jan 17 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.5-1
- Update to 2.13.5

* Mon Jan 16 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.4-2
- Disable the fatal-criticals, since it crashes too much 

* Fri Jan 13 2006 Matthias Clasen <mclasen@redhat.com> - 2.13.4-1
- Update to 2.13.4

* Thu Jan 12 2006 Ray Strode <rstrode@redhat.com> - 2.12.0-6
- Fix screen corruption around splash screen shape (bug 177502)

* Tue Dec 20 2005 John (J5) Palmieri <johnp@redhat.com> - 2.12.0-5
- Handle shaped window for splash screen

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Wed Nov  9 2005 Alexander Larsson <alexl@redhat.com> - 2.12.0-4
- Add gnome-user-share patch

* Tue Nov 8 2005 Ray Strode <rstrode@redhat.com> - 2.12.0-3
- fix up the dummy client ids to match the id passed initially
  passed to the programs in the default session 
  (broke in last update).

* Mon Oct 31 2005 Ray Strode <rstrode@redhat.com> - 2.12.0-2
- remove rhn applet from default session
- s/magicdev/gnome-volume-manager/

* Thu Sep  8 2005 Matthias Clasen <mclasen@redhat.com> - 2.12.0-1
- Update to 2.12.0

* Tue Sep  6 2005 Ray Strode <rstrode@redhat.com> - 2.11.91-3
- Don't take ownership of /usr/share/xsessions (bug 145791).

* Tue Aug 16 2005 Warren Togami <wtogami@redhat.com> - 2.11.91-2
- rebuild for new cairo

* Tue Aug  9 2005 Ray Strode <rstrode@redhat.com> - 2.11.91-1
- Update to upstream version 2.11.91 (fixes bug 165357).
- drop some patches

* Thu Apr 18 2005 Ray Strode <rstrode@redhat.com> - 2.10.0-2
- Install gnome.desktop to /usr/share/xsessions (bug 145791)

* Thu Mar 17 2005 Ray Strode <rstrode@redhat.com> - 2.10.0-1
- Update to upstream version 2.10.0

* Wed Feb  2 2005 Matthias Clasen <mclasen@redhat.com> 2.9.4-1
- Update to 2.9.4

* Mon Dec 20 2004 Daniel Reed <djr@redhat.com> 2.8.0-7
- rebuild for new libhowl.so.0 library (for GnomeMeeting 1.2) (this was a mistake)

* Tue Nov 02 2004 Ray Strode <rstrode@redhat.com> 2.8.0-6
- Rebuild for devel branch

 * Tue Nov 02 2004 Ray Strode <rstrode@redhat.com> 2.8.0-5
- Convert Tamil translation to UTF8 
  (Patch from Lawrence Lim <llim@redhat.com>, bug 135351)

* Fri Oct 08 2004 Ray Strode <rstrode@redhat.com> 2.8.0-4
- Add g-v-m to default session since it wasn't already (?).
- Remove g-v-m from default session on s390

* Thu Oct 07 2004 Ray Strode <rstrode@redhat.com> 2.8.0-3
- Check for NULL program name when looking for client
  match in session.

* Fri Sep 24 2004 Ray Strode <rstrode@redhat.com> 2.8.0-2
- Add "Session" item to More Preferences menu

* Fri Sep 17 2004 Ray Strode <rstrode@redhat.com> 2.8.0-1
- Update to 2.8.0 
- Remove "Session" item from Preferences menu

* Fri Sep 03 2004 Ray Strode <rstrode@redhat.com> 2.7.91-2
- Fix from Federico for infamous hanging splash screen problem.
  (http://bugzilla.gnome.org/show_bug.cgi?id=151664)

* Tue Aug 31 2004 Ray Strode <rstrode@redhat.com> 2.7.91-1
- Update to 2.7.91

* Wed Aug 18 2004 Ray Strode <rstrode@redhat.com> 2.7.4-3
- Change folder name from "autostart" to more aptly named
  "session-upgrades" from suggestion by Colin Walters.
- put non-upstream gconf key in rh_extensions

* Wed Aug 18 2004 Ray Strode <rstrode@redhat.com> 2.7.4-2
- Provide drop-a-desktop-file method of adding programs
  to the user's session.

* Fri Jul 30 2004 Ray Strode <rstrode@redhat.com> 2.7.4-1
- Update to 2.7.4

* Wed Jul 14 2004 root <markmc@localhost.localdomain> - 2.6.0-7
- Add patch to activate vino based on the "remote_access/enabled"
  preference

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Mon Jun 14 2004 Ray Strode <rstrode@redhat.com> 2.6.0-5
- Prevent having duplicate packages in different collections

* Mon Jun 14 2004 Ray Strode <rstrode@redhat.com> 2.6.0-4
- Use desktop-file-install instead of patching 
  session-properties.desktop.  Add X-Red-Hat-Base category.

* Thu Jun 10 2004 Ray Strode <rstrode@redhat.com> 2.6.0-3
- Add terminating list delimiter to OnlyShowIn entry of 
  session-properties.desktop

* Fri Apr 16 2004 Warren Togami <wtogami@redhat.com> 2.6.0-2
- #110725 BR automake14 autoconf gettext

* Wed Mar 31 2004 Mark McLoughlin <markmc@redhat.com> 2.6.0-1
- Update to 2.6.0

* Wed Mar 10 2004 Mark McLoughlin <markmc@redhat.com>
- Update to 2.5.91

* Tue Feb 24 2004 Mark McLoughlin <markmc@redhat.com> 2.5.90-1
- Update to 2.5.90
- Remove extraneous fontconfig BuildRequires
- Resolve conflicts with the icons and splash-repaint patches

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Mon Jan 26 2004 Alexander Larsson <alexl@redhat.com> 2.5.3-1
- Update to 2.5.3

* Wed Nov 05 2003 Than Ngo <than@redhat.com> 2.4.0-2
- don't show gnome-session-properties in KDE (bug #102533)

* Fri Aug 29 2003 Alexander Larsson <alexl@redhat.com> 2.3.7-3
- fix up gnome.desktop location

* Fri Aug 29 2003 Alexander Larsson <alexl@redhat.com> 2.3.7-2
- add gnome.desktop session for new gdm

* Wed Aug 27 2003 Alexander Larsson <alexl@redhat.com> 2.3.7-1
- update to 2.3.7
- require control-center (#100562)

* Fri Aug 15 2003 Alexander Larsson <alexl@redhat.com> 2.3.6.2-1
- update for gnome 2.3

* Sun Aug 10 2003 Elliot Lee <sopwith@redhat.com> 2.2.2-4
- Rebuild

* Tue Jul 22 2003 Jonathan Blandford <jrb@redhat.com>
- at-startup patch to add let at's start

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Tue Jun  3 2003 Jeff Johnson <jbj@redhat.com>
- add explicit epoch's where needed.

* Tue May 27 2003 Alexander Larsson <alexl@redhat.com> 2.2.2-1
- Update to 2.2.2
- Add XRandR backport
- Fix up old patches, patch7 was upstream

* Mon Feb 24 2003 Owen Taylor <otaylor@redhat.com> 2.2.0.2-5
- Wait for GSD to start before continuing with session

* Tue Feb 18 2003 Havoc Pennington <hp@redhat.com> 2.2.0.2-4
- repaint proper area of text in splash screen, #84527

* Tue Feb 18 2003 Havoc Pennington <hp@redhat.com> 2.2.0.2-3
- change icon for magicdev to one that exists in Bluecurve theme
  (part of #84491)

* Thu Feb 13 2003 Havoc Pennington <hp@redhat.com> 2.2.0.2-2
- load icons from icon theme

* Wed Feb  5 2003 Havoc Pennington <hp@redhat.com> 2.2.0.2-1
- 2.2.0.2

* Tue Feb  4 2003 Jonathan Blandford <jrb@redhat.com>
- remove extraneous separator.  Still ugly.

* Wed Jan 29 2003 Havoc Pennington <hp@redhat.com>
- add icons for the stuff in the default session #81489

* Wed Jan 22 2003 Tim Powers <timp@redhat.com>
- rebuilt

* Sat Jan 11 2003 Havoc Pennington <hp@redhat.com>
- 2.1.90
- drop purgedelay patch, as it was increased upstream (though only to 2 minutes instead of 5)

* Fri Dec  6 2002 Tim Waugh <twaugh@redhat.com> 2.1.2-2
- Add eggcups to default session.

* Wed Nov 13 2002 Havoc Pennington <hp@redhat.com>
- 2.1.2

* Tue Sep  3 2002 Owen Taylor <otaylor@redhat.com>
- Up purge delay for session manager to 5 minutes to avoid problem 
  with openoffice.org timing out

* Wed Aug 28 2002 Havoc Pennington <hp@redhat.com>
- put gdm session in here, conflict with old gdm
- use DITHER_MAX for dithering to make splash screen look good in 16
  bit

* Tue Aug 27 2002 Havoc Pennington <hp@redhat.com>
- fix missing icons and misaligned text in splash

* Fri Aug 23 2002 Tim Waugh <twaugh@redhat.com>
- Fix login sound disabling (bug #71664).

* Wed Aug 14 2002 Havoc Pennington <hp@redhat.com>
- put rhn applet in default session

* Wed Aug 14 2002 Havoc Pennington <hp@redhat.com>
- fix the session file, should speed up login a lot
- put magicdev in default session

* Thu Aug  8 2002 Havoc Pennington <hp@redhat.com>
- 2.0.5 with more translations

* Tue Aug  6 2002 Havoc Pennington <hp@redhat.com>
- 2.0.4
- remove gnome-settings-daemon from default session

* Wed Jul 31 2002 Havoc Pennington <hp@redhat.com>
- 2.0.3
- remove splash screen, require redhat-artwork instead

* Wed Jul 24 2002 Owen Taylor <otaylor@redhat.com>
- Set GTK_RC_FILES so we can change the gtk1 theme

* Tue Jul 16 2002 Havoc Pennington <hp@redhat.com>
- pass --with-halt-command=/usr/bin/poweroff
  --with-reboot-command=/usr/bin/reboot

* Tue Jun 25 2002 Owen Taylor <otaylor@redhat.com>
- Version 2.0.1, fixing missing po files

* Wed Jun 19 2002 Havoc Pennington <hp@redhat.com>
- put in new default session with pam-panel-icon
- disable schema install in make install, fixes rebuild failure.

* Sun Jun 16 2002 Havoc Pennington <hp@redhat.com>
- rebuild with new libraries

* Thu Jun 13 2002 Havoc Pennington <hp@redhat.com>
- rebuild in different environment

* Thu Jun 13 2002 Havoc Pennington <hp@redhat.com>
- add fix from Nalin to build require usermode

* Tue Jun 11 2002 Havoc Pennington <hp@redhat.com>
- 2.0.0

* Mon Jun 10 2002 Havoc Pennington <hp@redhat.com>
- install the schemas, so we get a logout dialog and splash
- put in the splash from 7.3

* Sun Jun 09 2002 Havoc Pennington <hp@redhat.com>
- rebuild in different environment

* Sun Jun 09 2002 Havoc Pennington <hp@redhat.com>
- rebuild in new environment, require newer gtk2

* Sun Jun  9 2002 Havoc Pennington <hp@redhat.com>
- remove obsoletes/provides gnome-core

* Fri Jun 07 2002 Havoc Pennington <hp@redhat.com>
- rebuild in different environment

* Wed Jun  5 2002 Havoc Pennington <hp@redhat.com>
- 1.5.21

* Sun May 26 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Tue May 21 2002 Havoc Pennington <hp@redhat.com>
- rebuild in different environment

* Tue May 21 2002 Havoc Pennington <hp@redhat.com>
- 1.5.19
- add more build reqs to chill out build system
- provide gnome-core

* Fri May  3 2002 Havoc Pennington <hp@redhat.com>
- obsolete gnome-core
- 1.5.18

* Fri Apr 19 2002 Havoc Pennington <hp@redhat.com>
- default to metacity

* Tue Apr 16 2002 Havoc Pennington <hp@redhat.com>
- Initial build.


