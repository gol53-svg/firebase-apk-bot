#!/bin/bash

# Set Java paths explicitly
export JAVA_HOME=/usr/lib/jvm/default-java
export PATH=$JAVA_HOME/bin:$PATH

# Verify Java
echo "Checking Java installation..."
java -version

if [ $? -ne 0 ]; then
    echo "ERROR: Java not found!"
    echo "Searching for Java..."
    
    # Find Java
    JAVA_PATH=$(find /usr/lib/jvm -name "java" -type f 2>/dev/null | head -1)
    
    if [ -n "$JAVA_PATH" ]; then
        export JAVA_HOME=$(dirname $(dirname $JAVA_PATH))
        export PATH=$JAVA_HOME/bin:$PATH
        echo "Found Java at: $JAVA_HOME"
        java -version
    else
        echo "Java not found anywhere!"
        exit 1
    fi
fi

# Start bot
echo "Starting Firebase APK Bot..."
python firebase_apk_bot.py
