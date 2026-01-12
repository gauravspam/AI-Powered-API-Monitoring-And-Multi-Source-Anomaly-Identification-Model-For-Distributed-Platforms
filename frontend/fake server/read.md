
first two commands to start the mock server
```bash
docker build -t my-js-server .
docker run -d -p 8080:8080 --name mock-server my-js-server
```

to start and stop the mock server
```bash
docker stop mock-server
docker start mock-server
```


when you dont need mock server delet with this commands
```bash
docker rm -f mock-server
docker rmi my-js-server
```





 |Task|Command |
 |------|------|
 |Stop all running containers| docker stop $(docker ps -aq) |
 |Remove all containers| docker rm $(docker ps -aq) |
 |Remove all images| docker rmi $(docker images -q) |