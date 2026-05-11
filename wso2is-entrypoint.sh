#!/bin/bash
# Custom entrypoint for WSO2IS to ensure PostgreSQL driver is available

set -e

WSO2_HOME="/home/wso2carbon/wso2is-7.1.0"
DRIVER_JAR="postgresql-42.7.2.jar"
DRIVER_URL="https://jdbc.postgresql.org/download/${DRIVER_JAR}"

echo "=== WSO2IS PostgreSQL Driver Setup ==="

# Check if driver already exists in lib/
if [ -f "$WSO2_HOME/lib/$DRIVER_JAR" ]; then
    echo "✅ PostgreSQL driver already exists in $WSO2_HOME/lib/"
else
    echo "⬇️  Downloading PostgreSQL JDBC driver..."
    mkdir -p "$WSO2_HOME/lib"
    wget --no-verbose "$DRIVER_URL" -O "$WSO2_HOME/lib/$DRIVER_JAR"
    chmod 644 "$WSO2_HOME/lib/$DRIVER_JAR"
    echo "✅ PostgreSQL driver installed to $WSO2_HOME/lib/"
fi

# Also ensure it's in repository/components/lib/
if [ ! -f "$WSO2_HOME/repository/components/lib/$DRIVER_JAR" ]; then
    echo "📋 Copying driver to repository/components/lib/..."
    mkdir -p "$WSO2_HOME/repository/components/lib"
    cp "$WSO2_HOME/lib/$DRIVER_JAR" "$WSO2_HOME/repository/components/lib/"
    chmod 644 "$WSO2_HOME/repository/components/lib/$DRIVER_JAR"
fi

echo "📍 Verifying driver locations:"
ls -lh "$WSO2_HOME/lib/$DRIVER_JAR"
ls -lh "$WSO2_HOME/repository/components/lib/$DRIVER_JAR"

echo "✅ PostgreSQL driver setup complete"
echo ""

# Call the original WSO2IS entrypoint
exec /home/wso2carbon/docker-entrypoint.sh "$@"
