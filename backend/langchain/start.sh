if [ ! -d "./node_modules" ]; then
    npm install
fi

# $RUNNING_ENV must be exported in the environment
npx pm2 start --no-daemon "./config/$RUNNING_ENV.pm2.json"