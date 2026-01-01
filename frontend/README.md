first install all the modukes by 
```bash
npm install
```



to start the frontend run following command in terminal

```bash
npm run dev
```

this will start the frontend server on ```http://localhost:5173/```



with docker 
```bash
docker build -t api-monitoring-frontend .
docker run -d -p 8080:80 api-monitoring-frontend
```

this will start the frontend server on ```http://localhost:8080/```
