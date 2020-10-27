# FlickrGroupAddr

## UI Dev

### Docker 

[Reference](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04)

```
$ sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
$ sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
$ sudo apt-get -y update
$ sudo apt-get -y install docker-ce
$ sudo usermod -aG docker ${USER}
$ logout
```

### LetsEncrypt

```
$ sudo apt-get -y install certbot
$ sudo certbot certonly --standalone -d groupaddr.sixbuckssolutions.com
```

### Git

```
$ ssh-keygen -b 4096
```

Copy the public key to Github

```
$ mkdir ~/git
$ cd ~/git
$ git clone git@github.com:TerryOtt/FlickrGroupAddr.git
```

### NGINX Alpine with SSL

[Source](https://medium.com/myriatek/using-docker-to-run-a-simple-nginx-server-75a48d74500b)

```
$ docker pull nginx:alpine
$ mkdir certs
$ sudo cp /etc/letsencrypt/live/groupaddr.sixbuckssolutions.com/fullchain.pem certs/groupaddr.sixbuckssolutions.com.crt
$ 
```

### Dockerfile

```
FROM nginx:alpine
COPY nginx.con /etc/nginx.conf.d/
COPY *.html /usr/share/nginx/html/
COPY css/* /usr/share/nginx/html/css/
COPY js/* /usr/share/nginx/html/js/
EXPOSE 443
```

### Build/Run

```
$ cd static
$ docker build -t groupaddr .
$ sudo docker run --rm -it -v /etc/letsencrypt/archive/groupaddr.sixbuckssolutions.com:/etc/nginx/certs -p 443:443 groupaddr 
```


## REST API Dev

### Python modules

```
$ sudo apt-get -y install python3-pip certbot flickr_api
$ sudo pip3 install tornado
```

### LetsEncrypt

```
$ sudo apt-get -y install certbot python3-certbot
$ sudo certbot certonly --standalone -d groupaddrapi.sixbuckssolutions.com
```


