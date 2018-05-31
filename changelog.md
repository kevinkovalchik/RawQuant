# Changelog
All notable changes to this project will be documented in this file.

## [unreleased]
-When "Monoisotopic Precursor Selection" is turned off during MS acquisition, raw files contain
0.0 values for the Monoisotopic M/Z. When this happens, we now report the mass value that triggers
the data-dependent scan. Not ideal, so future improvement might be recalculating the precursor mass.

## [0.2.0]
-Metrics files are now tab-delimited

-Added retention time to MGF file header

-Fixed a bug which caused issues when there was an isolation window offset

-RawQuant migrated to using RawFileReader instead of MSFileReader

## [0.1.4]
Changes not tracked prior to this version
