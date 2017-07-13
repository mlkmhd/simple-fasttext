apt-get install screen

cd fastText
make

cd ..

wget -c "http://download.redis.io/releases/redis-3.2.9.tar.gz"
tar -xzf redis-3.2.9.tar.gz
mv redis-3.2.9 redis
rm redis-3.2.9.tar.gz

cd redis
make
screen src/redis-server


