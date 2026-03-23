# Open Eurostat Microdata Schema Inventory

Date: 2026-03-23

This folder inventories the Eurostat public microdata that are directly downloadable without registration, based on the official Eurostat public-microdata pages and codebooks.

Files:
- `eurostat_public_lfs_variables.csv`: EU-LFS public-use variables from the official LFS PUF metadata workbook.
- `eurostat_public_silc_variables.csv`: EU-SILC public-use variables from the official SILC PUF metadata workbook.

Important caveats:
- EU-LFS public microdata are fully anonymised public-use files.
- EU-SILC public microdata are fully synthetic and Eurostat states they must not be used for statistical inference or valid publication analysis.
- `observed_in_AT_2013...` columns show whether the variable appears in one representative open file checked directly from the downloadable Austrian 2013 public files. Variable availability can vary by year and file type.

Source pages:
- https://ec.europa.eu/eurostat/web/microdata/public-microdata/labour-force-survey
- https://ec.europa.eu/eurostat/web/microdata/public-microdata/statistics-on-income-and-living-conditions
