# Open Firmware Configuration for the OLPC
ofw_config = """\
\ Boot script for USB boot
\ Authors: Mitch Bradley <wmb AT laptop DOT org>
hex  rom-pa fffc7 + 4 $number drop  h# 2e19 < [if]
  patch 2drop erase claim-params
  : high-ramdisk  ( -- )
     cv-load-ramdisk
     h# 22c +lp l@ 1+   memory-limit  umin  /ramdisk - ffff.f000 and ( new-ramdisk-adr )
     ramdisk-adr over  /ramdisk move                    ( new-ramdisk-adr )
     to ramdisk-adr
  ;
  ' high-ramdisk to load-ramdisk
[then]

: set-bootpath-dev  ( -- )
   " /chosen" find-package  if                       ( phandle )
      " bootpath" rot  get-package-property  0=  if  ( propval$ )
         get-encoded-string                          ( bootpath$ )
         [char] \ left-parse-string  2nip            ( dn$ )
         dn-buf place                                ( )
      then
   then

   " /sd"  dn-buf  count  sindex  0>=   if
          " sd:"
   else
          " u:"
   then
   " BOOTPATHDEV" $set-macro
;

set-bootpath-dev
" %s" to boot-file
" ${BOOTPATHDEV}\syslinux\initrd0.img" expand$ to ramdisk
" ${BOOTPATHDEV}\syslinux\\vmlinuz0" expand$ to boot-device
unfreeze
dcon-unfreeze
boot
"""
