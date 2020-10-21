#!/bin/bash

echo "Attempting to clear all tables from bioclustedb database ${USER}"

# Clear all tables
mysql -h bioclusterdb -u $USER -p << EOF
USE ${USER}
SELECT 
  CONCAT('DROP TABLE ',GROUP_CONCAT(CONCAT(table_schema,'.',table_name)),';')
  INTO @dropcmd
  FROM information_schema.tables
  WHERE table_schema='${USER}';

PREPARE str FROM @dropcmd; EXECUTE str; DEALLOCATE PREPARE str;
EOF

# Check if everything went well
if [ $? -eq 0 ]; then
  echo "SUCCESS:: Cleared all tables from databases ${USER}"
else
  echo "ERROR:: "
  exit $?
fi
