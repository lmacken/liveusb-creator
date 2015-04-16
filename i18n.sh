#!/bin/bash
# Author: ltinkl@redhat.com

PACKAGE="liveusb-creator"

# Create a list of files to scan
GETTEXT_FILES=$(mktemp --tmpdir $PACKAGE.lst.XXXXX)
trap 'rm -f "$GETTEXT_FILES"' EXIT
find \( -name '*.py' -o -name '*.qml' -o -name '*.js' \) \
    -a ! \( -path './debian/*' -o -path './builddir/*' -o -path './build/*' -o -path './.git/*' -o -path './tests/*' \) | sort \
> $GETTEXT_FILES

# Generate pot from our list
xgettext \
    --output po/$PACKAGE.pot \
    --files-from $GETTEXT_FILES \
    --qt -L Java -L Python \
    --package-name="$PACKAGE" \
    --add-comments=TRANSLATORS \
    --keyword=qsTranslate \
    --keyword=qsTranslate:1c,2 \
    --copyright-holder="RedHat Inc." \
    --from-code="UTF-8"
