# MySQL Command Helper
# Remember to keep the text quoted
if [ -z "$1" -o -z "$2" ]; then
  echo "Usage: ./mysql_command_injector.sh 'QUERY_TEXT' 'DB_NAME'"
  exit 1;
fi
QUERY_TEXT="$1"
DB_NAME="$2"
#staging
#mysql -u doer -pYxPyixXLUEtFUR3z
#mysql -u doer -pYxPyixXLUEtFUR3z -e "$FIND_ALL_TABLES" 2>/dev/null
mysql -u doer -pYxPyixXLUEtFUR3z -e "$QUERY_TEXT" "$DB_NAME" 2>/dev/null