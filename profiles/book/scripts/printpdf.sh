#!/bin/sh
# Convert the print PDF of the book for press: CMYK with an output intent, grey text as K only (no rich black).
#
# Usage: scripts/printpdf.sh book.pdf print.pdf [press-profile.icc]
#
# Without a profile the Ghostscript default (a SWOP-like CMYK profile) is used. For the printer's press pass its
# profile (FOGRA39 or FOGRA51 in Europe, SWOP or GRACoL in the United States) and soft-proof the result with it before
# sending the file.
set -eu
input="$1"
output="$2"
version=$(gs --version)
share=$(dirname "$(dirname "$(command -v gs)")")/share/ghostscript/$version/iccprofiles
profile="${3:-$share/default_cmyk.icc}"
gs -dBATCH -dNOPAUSE -dQUIET -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress -dCompatibilityLevel=1.6 \
  -sColorConversionStrategy=CMYK -dProcessColorModel=/DeviceCMYK \
  -sOutputICCProfile="$profile" -sGrayICCProfile="$share/gray_to_k.icc" \
  -dEmbedAllFonts=true -dSubsetFonts=true -sOutputFile="$output" "$input"
echo "wrote $output with profile $profile"
